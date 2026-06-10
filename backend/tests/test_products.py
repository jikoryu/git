"""Tests for product endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient, auth_headers: dict):
    # First, register a product via the lookup endpoint (will create mock product)
    # Since real scraping isn't available in tests, we search for products
    # already in the database. For now, search returns empty list gracefully.
    resp = await client.get(
        "/api/v1/products/search", params={"q": "test"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/products/non-existent-id", headers=auth_headers
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_price_history_not_found(client: AsyncClient, auth_headers: dict):
    """Price history for non-existent product should return 404."""
    resp = await client.get(
        "/api/v1/products/non-existent-id/history", headers=auth_headers
    )
    assert resp.status_code == 404
