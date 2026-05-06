import csv
import io
import json
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path


class ArchiveParseError(ValueError):
    pass


def extract_commercial_offers(archive_content: bytes) -> dict:
    if not zipfile.is_zipfile(io.BytesIO(archive_content)):
        raise ArchiveParseError("Uploaded file must be a zip archive")

    items: list[dict] = []
    suppliers: set[str] = set()

    with zipfile.ZipFile(io.BytesIO(archive_content)) as archive:
        file_names = [name for name in archive.namelist() if not name.endswith("/")]
        if not file_names:
            raise ArchiveParseError("Archive is empty")

        for file_name in file_names:
            suffix = Path(file_name).suffix.lower()
            raw_content = archive.read(file_name)

            if suffix == ".csv":
                parsed_items = _parse_csv(raw_content, file_name)
            elif suffix == ".json":
                parsed_items = _parse_json(raw_content, file_name)
            elif suffix == ".txt":
                parsed_items = _parse_txt(raw_content, file_name)
            else:
                continue

            for item in parsed_items:
                item["source_file"] = file_name
                suppliers.add(item["supplier"])
                items.append(item)

    if not items:
        raise ArchiveParseError("Archive does not contain supported offer files")

    return {
        "positions": items,
        "suppliers": sorted(suppliers),
        "total_positions": len(items),
        "min_price": min(item["price"] for item in items),
    }


def _parse_csv(raw_content: bytes, file_name: str) -> list[dict]:
    text = _decode(raw_content, file_name)
    reader = csv.DictReader(io.StringIO(text))
    return [_normalize_row(row, file_name) for row in reader]


def _parse_json(raw_content: bytes, file_name: str) -> list[dict]:
    text = _decode(raw_content, file_name)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ArchiveParseError(f"{file_name}: invalid json") from exc

    if isinstance(data, dict):
        rows = data.get("positions") or data.get("items") or data.get("offers")
    else:
        rows = data

    if not isinstance(rows, list):
        raise ArchiveParseError(f"{file_name}: json must contain a list of offers")

    return [_normalize_row(row, file_name) for row in rows]


def _parse_txt(raw_content: bytes, file_name: str) -> list[dict]:
    text = _decode(raw_content, file_name)
    items = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(";")]
        if len(parts) != 3:
            raise ArchiveParseError(
                f"{file_name}:{line_number}: expected supplier;name;price"
            )
        supplier, name, price = parts
        items.append(_normalize_row({"supplier": supplier, "name": name, "price": price}, file_name))
    return items


def _normalize_row(row: dict, file_name: str) -> dict:
    if not isinstance(row, dict):
        raise ArchiveParseError(f"{file_name}: each offer must be an object")

    supplier = row.get("supplier") or row.get("vendor") or row.get("company")
    name = row.get("name") or row.get("product") or row.get("item")
    price = row.get("price") or row.get("cost")

    if not supplier or not name or price is None:
        raise ArchiveParseError(
            f"{file_name}: each offer must have supplier, name and price"
        )

    try:
        normalized_price = Decimal(str(price).replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise ArchiveParseError(f"{file_name}: invalid price {price}") from exc

    if normalized_price < 0:
        raise ArchiveParseError(f"{file_name}: price must not be negative")

    return {
        "supplier": str(supplier).strip(),
        "name": str(name).strip(),
        "price": float(normalized_price),
    }


def _decode(raw_content: bytes, file_name: str) -> str:
    for encoding in ("utf-8-sig", "cp1251"):
        try:
            return raw_content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ArchiveParseError(f"{file_name}: unsupported encoding")
