import logging
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.core.config import Settings

logger = logging.getLogger(__name__)
from app.schemas.sec import (
    FilingSection,
    ParsedSecFilingResponse,
    SecFilingMetadata,
    SecFilingsListResponse,
)


class SecEdgarError(Exception):
    """Exception raised for errors during SEC EDGAR interaction or parsing."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# 10-K Section definitions: (item_id, display_title, start_regex, end_regex)
SECTIONS_10K = [
    (
        "item_1",
        "Item 1. Business",
        r"(?:ITEM|Item)\s+1\.\s+(?:BUSINESS|Business)",
        r"(?:ITEM|Item)\s+1A\.\s+(?:RISK\s+FACTORS|Risk\s+Factors)",
    ),
    (
        "item_1a",
        "Item 1A. Risk Factors",
        r"(?:ITEM|Item)\s+1A\.\s+(?:RISK\s+FACTORS|Risk\s+Factors)",
        r"(?:ITEM|Item)\s+(?:1B|2)\.\s+",
    ),
    (
        "item_7",
        "Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations",
        r"(?:ITEM|Item)\s+7\.\s+(?:MANAGEMENT['’]S\s+DISCUSSION|Management['’]s\s+Discussion)",
        r"(?:ITEM|Item)\s+7A\.\s+(?:QUANTITATIVE|Quantitative)|(?:ITEM|Item)\s+8\.\s+(?:FINANCIAL|Financial)",
    ),
    (
        "item_7a",
        "Item 7A. Quantitative and Qualitative Disclosures About Market Risk",
        r"(?:ITEM|Item)\s+7A\.\s+(?:QUANTITATIVE|Quantitative)",
        r"(?:ITEM|Item)\s+8\.\s+(?:FINANCIAL|Financial)",
    ),
    (
        "item_8",
        "Item 8. Financial Statements and Supplementary Data",
        r"(?:ITEM|Item)\s+8\.\s+(?:FINANCIAL\s+STATEMENTS|Financial\s+Statements)",
        r"(?:ITEM|Item)\s+9\.\s+",
    ),
]

# 10-Q Section definitions
SECTIONS_10Q = [
    (
        "part1_item1",
        "Part I, Item 1. Financial Statements",
        r"(?:ITEM|Item)\s+1\.\s+(?:FINANCIAL\s+STATEMENTS|Financial\s+Statements)",
        r"(?:ITEM|Item)\s+2\.\s+(?:MANAGEMENT['’]S\s+DISCUSSION|Management['’]s\s+Discussion)",
    ),
    (
        "part1_item2",
        "Part I, Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations",
        r"(?:ITEM|Item)\s+2\.\s+(?:MANAGEMENT['’]S\s+DISCUSSION|Management['’]s\s+Discussion)",
        r"(?:ITEM|Item)\s+3\.\s+|(?:ITEM|Item)\s+4\.\s+|(?:PART|Part)\s+II",
    ),
    (
        "part2_item1a",
        "Part II, Item 1A. Risk Factors",
        r"(?:ITEM|Item)\s+1A\.\s+(?:RISK\s+FACTORS|Risk\s+Factors)",
        r"(?:ITEM|Item)\s+[2-6]\.\s+",
    ),
]


class SecEdgarService:
    """Service to interact with the SEC EDGAR API and parse 10-K / 10-Q filings."""

    SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
    SEC_SUBMISSIONS_BASE_URL = "https://data.sec.gov/submissions"
    SEC_ARCHIVES_BASE_URL = "https://www.sec.gov/Archives/edgar/data"

    def __init__(self, settings: Settings):
        self.settings = settings
        self._ticker_cache: dict[str, tuple[str, str]] = {}

    def _get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.settings.sec_edgar_user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov" if "www.sec.gov" in self.SEC_TICKERS_URL else "data.sec.gov",
        }

    def _get_client(self) -> httpx.Client:
        return httpx.Client(
            headers={"User-Agent": self.settings.sec_edgar_user_agent},
            timeout=15.0,
            follow_redirects=True,
        )

    def load_tickers_mapping(self) -> dict[str, tuple[str, str]]:
        """Fetch and cache ticker to (10-digit CIK, company_name) mapping from SEC."""
        if self._ticker_cache:
            return self._ticker_cache

        client = self._get_client()
        try:
            response = client.get(self.SEC_TICKERS_URL)
            if response.status_code != 200:
                raise SecEdgarError(
                    f"SEC EDGAR returned status {response.status_code} while fetching company tickers.",
                    status_code=502,
                )
            data: dict[str, dict[str, Any]] = response.json()
            cache: dict[str, tuple[str, str]] = {}
            for item in data.values():
                ticker = str(item.get("ticker", "")).strip().upper()
                cik_num = item.get("cik_str")
                title = str(item.get("title", "")).strip()
                if ticker and cik_num is not None:
                    cik_str = str(cik_num).zfill(10)
                    cache[ticker] = (cik_str, title)
            self._ticker_cache = cache
            return self._ticker_cache
        except httpx.HTTPError as exc:
            raise SecEdgarError(
                f"Failed to connect to SEC EDGAR tickers registry: {exc!s}",
                status_code=502,
            ) from exc
        finally:
            client.close()

    def get_cik_by_ticker(self, ticker: str) -> tuple[str, str]:
        """Resolve ticker to (10-digit CIK, company_name)."""
        ticker_clean = ticker.strip().upper()
        mapping = self.load_tickers_mapping()
        if ticker_clean not in mapping:
            raise SecEdgarError(
                f"Ticker '{ticker_clean}' not found in SEC EDGAR directory.",
                status_code=404,
            )
        return mapping[ticker_clean]

    def get_company_filings(
        self,
        ticker: str,
        form_types: list[str] | None = None,
        limit: int = 10,
    ) -> SecFilingsListResponse:
        """Fetch recent filings for a company ticker, optionally filtered by form types (e.g. ['10-K', '10-Q'])."""
        cik, company_name = self.get_cik_by_ticker(ticker)
        cik_int_str = str(int(cik))
        url = f"{self.SEC_SUBMISSIONS_BASE_URL}/CIK{cik}.json"

        client = self._get_client()
        try:
            response = client.get(url)
            if response.status_code == 404:
                raise SecEdgarError(
                    f"Submissions data for CIK {cik} ({ticker}) not found on SEC EDGAR.",
                    status_code=404,
                )
            if response.status_code != 200:
                raise SecEdgarError(
                    f"SEC EDGAR returned status {response.status_code} for CIK {cik}.",
                    status_code=502,
                )
            data = response.json()
        except httpx.HTTPError as exc:
            raise SecEdgarError(
                f"Failed to fetch submissions from SEC EDGAR: {exc!s}",
                status_code=502,
            ) from exc
        finally:
            client.close()

        recent = data.get("filings", {}).get("recent", {})
        accession_numbers = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        forms = recent.get("form", [])
        primary_docs = recent.get("primaryDocument", [])
        descriptions = recent.get("primaryDocDescription", [])

        normalized_form_filter = (
            [f.strip().upper() for f in form_types] if form_types else None
        )

        filings: list[SecFilingMetadata] = []
        for i in range(len(accession_numbers)):
            form = forms[i] if i < len(forms) else ""
            if (
                normalized_form_filter
                and form.strip().upper() not in normalized_form_filter
            ):
                continue

            acc_num = accession_numbers[i]
            acc_clean = acc_num.replace("-", "")
            prim_doc = primary_docs[i] if i < len(primary_docs) else ""
            filing_date = filing_dates[i] if i < len(filing_dates) else ""
            report_date = report_dates[i] if i < len(report_dates) else None
            desc = descriptions[i] if i < len(descriptions) else None

            doc_url = f"{self.SEC_ARCHIVES_BASE_URL}/{cik_int_str}/{acc_clean}/{prim_doc}"

            filings.append(
                SecFilingMetadata(
                    accession_number=acc_num,
                    form_type=form,
                    filing_date=filing_date,
                    report_date=report_date,
                    primary_document=prim_doc,
                    document_url=doc_url,
                    description=desc,
                )
            )

            if len(filings) >= limit:
                break

        return SecFilingsListResponse(
            ticker=ticker.upper(),
            cik=cik,
            company_name=company_name,
            filings=filings,
            total_count=len(filings),
        )

    def _clean_html_to_text(self, html_content: str) -> str:
        """Convert HTML document into clean plain text."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Strip scripts, styles, metadata
        for tag in soup(["script", "style", "head", "noscript", "meta"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        # Normalize non-breaking spaces and other special spaces
        text = text.replace("\xa0", " ").replace("\u200b", "")
        # Remove consecutive blank lines
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        # Collapse horizontal whitespace
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _extract_sections(
        self,
        clean_text: str,
        form_type: str,
        ticker: str | None = None,
        accession_number: str | None = None,
    ) -> dict[str, FilingSection]:
        """Extract structured sections based on 10-K or 10-Q standard Item definitions."""
        is_10q = "10-Q" in form_type.upper()
        definitions = SECTIONS_10Q if is_10q else SECTIONS_10K

        extracted: dict[str, FilingSection] = {}

        for item_id, title, start_pattern, end_pattern in definitions:
            # Find all start matches
            start_matches = list(
                re.finditer(start_pattern, clean_text, flags=re.IGNORECASE)
            )
            if not start_matches:
                logger.warning(
                    "Section start pattern not found for '%s' (%s) in %s filing (ticker: %s, accession: %s).",
                    item_id,
                    title,
                    form_type,
                    ticker or "unknown",
                    accession_number or "unknown",
                )
                continue

            # To avoid Table of Contents matches, prefer occurrences with substantial following text
            best_section_text = ""
            for start_match in start_matches:
                start_pos = start_match.start()
                subsequent_text = clean_text[start_pos:]

                # Search for the section ending pattern
                end_match = re.search(
                    end_pattern, subsequent_text[start_match.end() - start_pos :], flags=re.IGNORECASE
                )
                if end_match:
                    end_pos = start_match.end() + end_match.start()
                    candidate = clean_text[start_pos:end_pos].strip()
                else:
                    # Fallback: take up to 20,000 characters if no ending matched
                    candidate = clean_text[start_pos : start_pos + 20000].strip()

                # Filter out short TOC entries (< 200 chars)
                if len(candidate) > len(best_section_text):
                    best_section_text = candidate

            if best_section_text and len(best_section_text) > 40:
                extracted[item_id] = FilingSection(
                    item_id=item_id,
                    title=title,
                    content=best_section_text,
                    character_count=len(best_section_text),
                )
            else:
                logger.warning(
                    "Extracted section '%s' (%s) was empty or too short (%d chars) in %s filing (ticker: %s, accession: %s).",
                    item_id,
                    title,
                    len(best_section_text),
                    form_type,
                    ticker or "unknown",
                    accession_number or "unknown",
                )

        return extracted

    def fetch_and_parse_filing(
        self,
        ticker: str,
        accession_number: str,
        form_type: str | None = None,
    ) -> ParsedSecFilingResponse:
        """Fetch full HTML/text filing document from SEC archives and extract key sections."""
        cik, company_name = self.get_cik_by_ticker(ticker)
        cik_int_str = str(int(cik))
        acc_clean = accession_number.replace("-", "")

        # Lookup filing metadata to find the primary document name
        filings_data = self.get_company_filings(ticker=ticker, limit=50)
        matching_meta = next(
            (f for f in filings_data.filings if f.accession_number == accession_number),
            None,
        )

        detected_form_type = (
            form_type
            or (matching_meta.form_type if matching_meta else None)
            or "10-K"
        )
        filing_date = matching_meta.filing_date if matching_meta else ""
        report_date = matching_meta.report_date if matching_meta else None
        primary_doc = matching_meta.primary_document if matching_meta else ""

        client = self._get_client()
        try:
            # If primary document was found in submissions metadata
            doc_url = (
                f"{self.SEC_ARCHIVES_BASE_URL}/{cik_int_str}/{acc_clean}/{primary_doc}"
                if primary_doc
                else f"{self.SEC_ARCHIVES_BASE_URL}/{cik_int_str}/{acc_clean}/{accession_number}.txt"
            )

            response = client.get(doc_url)
            if response.status_code == 404 and primary_doc:
                # Fallback to complete submission text file
                fallback_url = f"{self.SEC_ARCHIVES_BASE_URL}/{cik_int_str}/{acc_clean}/{accession_number}.txt"
                response = client.get(fallback_url)

            if response.status_code != 200:
                raise SecEdgarError(
                    f"SEC EDGAR returned status {response.status_code} while downloading document {doc_url}.",
                    status_code=502,
                )
            raw_content = response.text
        except httpx.HTTPError as exc:
            raise SecEdgarError(
                f"Failed to download filing from SEC EDGAR: {exc!s}",
                status_code=502,
            ) from exc
        finally:
            client.close()

        clean_text = self._clean_html_to_text(raw_content)
        sections = self._extract_sections(
            clean_text=clean_text,
            form_type=detected_form_type,
            ticker=ticker,
            accession_number=accession_number,
        )

        preview_length = min(1500, len(clean_text))
        raw_preview = clean_text[:preview_length].strip()

        return ParsedSecFilingResponse(
            ticker=ticker.upper(),
            cik=cik,
            company_name=company_name,
            form_type=detected_form_type,
            accession_number=accession_number,
            filing_date=filing_date,
            report_date=report_date,
            sections=sections,
            raw_text_preview=raw_preview,
        )
