# permite hacer referencia a una clase antes de crearla
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

SESSION_ROOT = Path(__file__).resolve().parents[1]
ESCI_DATA_DIRECTORY = SESSION_ROOT / "data"
PRODUCTS_PATH = ESCI_DATA_DIRECTORY / "catalogo_muestra.csv"
JUDGMENTS_PATH = ESCI_DATA_DIRECTORY / "relevancias_desarrollo.csv"
ESCI_MANIFEST_PATH = ESCI_DATA_DIRECTORY / "manifest.json"

ESCI_GAINS = {"E": 3, "S": 2, "C": 1, "I": 0}
ESCI_LABEL_NAMES = {
    "E": "Exact",
    "S": "Substitute",
    "C": "Complement",
    "I": "Irrelevant",
}

PRODUCT_COLUMNS = {
    "record_id",
    "product_id",
    "title",
    "brand",
    "color",
    "locale",
    "text",
    "catalog_version",
    "active"
}

JUDGMENT_COLUMNS = {
    "query_id",
    "product_id",
    "esci_label",
    "relevance"
}

@dataclass(frozen=True, slots=True)
class EsciSample:
    products: pd.DataFrame
    judgments: pd.DataFrame


def clean_optional_text(value: object) -> str:
    """sustituye nulos por cadenas vacías"""
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def compose_product_text(product: pd.Series) -> str:
    """combina los campos relevantes para la búsqueda en un único texto."""
    title = clean_optional_text(product["title"])
    brand = clean_optional_text(product["brand"])
    color = clean_optional_text(product["color"])
    text = clean_optional_text(product["text"])

    sections = [title]
    if brand:
        sections.append(f"Marca: {brand}")
    if color:
        sections.append(f"Color: {color}")
    if text:
        sections.append(text)
    return ". ".join(section for section in sections if section)


def add_searchable_text(products: pd.DataFrame) -> pd.DataFrame:
    """añade columna nueva con campos relevantes para búsqueda"""
    enriched_products = products.copy()
    enriched_products["searchable_text"] = enriched_products.apply(
        compose_product_text,
        axis="columns",
    )
    return enriched_products


def load_esci_sample(
    products_path: str | Path = PRODUCTS_PATH,
    judgments_path: str | Path = JUDGMENTS_PATH,
) -> EsciSample:

    # leemos productos y relevancias
    products = pd.read_csv(products_path, keep_default_na=True)
    judgments = pd.read_csv(judgments_path, keep_default_na=True)

    # comprobamos que no faltan columnas obligatorias
    missing_product_columns = PRODUCT_COLUMNS - set(products.columns)
    missing_judgment_columns = JUDGMENT_COLUMNS - set(judgments.columns)
    if missing_product_columns:
        raise ValueError(f"Missing product columns: {sorted(missing_product_columns)}")
    if missing_judgment_columns:
        raise ValueError(
            f"Missing judgment columns: {sorted(missing_judgment_columns)}"
        )
    # comprueba ids duplicados
    if products["product_id"].duplicated().any():
        raise ValueError("products.csv contains duplicate product IDs")
    # comprueba etiquetas ESCI válidas
    if not set(judgments["esci_label"]).issubset(ESCI_GAINS):
        raise ValueError("judgments.csv contains unknown ESCI labels")
    
    # obtenemos ids del catálogo 
    product_ids = set(products["product_id"])
    # productos evaluados que no existen en el catálogo
    missing_products = set(judgments["product_id"]) - product_ids
    # comprueba si hay referencias a productos inexistentes
    if missing_products:
        raise ValueError(
            f"Judgments reference {len(missing_products)} missing products"
        )

    # añade columna con campos relevantes para la búsqueda
    # ordena por id y reinicia índices
    normalized_products = add_searchable_text(products).sort_values(
        "product_id", ignore_index=True
    )
    # ordena por id y reinicia índices
    normalized_judgments = judgments.sort_values(
        ["query_id"], ignore_index=True
    )
    return EsciSample(normalized_products, normalized_judgments)
