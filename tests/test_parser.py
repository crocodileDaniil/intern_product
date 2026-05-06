import io
import json
import unittest
import zipfile

from app.services.parser import ArchiveParseError, extract_commercial_offers


def make_zip(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


class ParserTestCase(unittest.TestCase):
    def test_extracts_csv_offers(self):
        archive = make_zip(
            {
                "offers.csv": (
                    "supplier,name,price\n"
                    "ООО Ромашка,Ноутбук,1000.50\n"
                    "ООО Вектор,Ноутбук аналог,900\n"
                )
            }
        )

        result = extract_commercial_offers(archive)

        self.assertEqual(result["total_positions"], 2)
        self.assertEqual(result["suppliers"], ["ООО Вектор", "ООО Ромашка"])
        self.assertEqual(result["min_price"], 900.0)

    def test_extracts_json_offers(self):
        archive = make_zip(
            {
                "offers.json": json.dumps(
                    {
                        "positions": [
                            {"supplier": "A", "name": "Printer", "price": "12500"}
                        ]
                    }
                )
            }
        )

        result = extract_commercial_offers(archive)

        self.assertEqual(result["positions"][0]["supplier"], "A")
        self.assertEqual(result["positions"][0]["price"], 12500.0)

    def test_extracts_txt_offers(self):
        archive = make_zip({"offers.txt": "Supplier;Paper;320.5\n"})

        result = extract_commercial_offers(archive)

        self.assertEqual(result["positions"][0]["name"], "Paper")

    def test_rejects_invalid_archive(self):
        with self.assertRaises(ArchiveParseError):
            extract_commercial_offers(b"not a zip")

    def test_rejects_missing_price(self):
        archive = make_zip({"offers.csv": "supplier,name,price\nA,Item,\n"})

        with self.assertRaises(ArchiveParseError):
            extract_commercial_offers(archive)


if __name__ == "__main__":
    unittest.main()
