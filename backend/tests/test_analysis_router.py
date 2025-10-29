# ABOUTME: Integration tests for Analysis API endpoints (Epic 8 - F8.3-001)
# ABOUTME: Tests global, position, and forecast analysis endpoints

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient
from main import app


class TestGlobalAnalysisEndpoint:
    """Integration tests for /api/analysis/global endpoint."""

    @pytest.fixture
    def mock_analysis_service(self, monkeypatch):
        """Mock AnalysisService to avoid Claude API calls."""
        async def mock_generate_global_analysis(force_refresh=False):
            return {
                'analysis': '## Market Sentiment\n\nMarkets showing positive momentum...',
                'generated_at': datetime.utcnow(),
                'tokens_used': 1523,
                'cached': False
            }

        # Patch the entire get_analysis_service dependency
        from analysis_router import get_analysis_service

        mock_service = MagicMock()
        mock_service.generate_global_analysis = mock_generate_global_analysis

        async def mock_get_service(db=None):
            return mock_service

        monkeypatch.setattr('analysis_router.get_analysis_service', lambda: mock_service)

        return mock_service

    def test_get_global_analysis_success(self, mock_analysis_service):
        """Test successful global analysis generation."""
        client = TestClient(app)

        # Mock the analysis service at the module level
        from analysis_router import router
        original_dependency = router.dependency_overrides.copy()

        # Override the dependency
        async def override_analysis_service():
            return mock_analysis_service

        from analysis_router import get_analysis_service
        router.dependency_overrides[get_analysis_service] = override_analysis_service

        try:
            response = client.get("/api/analysis/global")

            assert response.status_code == 200
            data = response.json()

            assert 'analysis' in data
            assert 'generated_at' in data
            assert 'tokens_used' in data
            assert 'cached' in data

            assert data['tokens_used'] == 1523
            assert data['cached'] is False
            assert 'Market Sentiment' in data['analysis']
        finally:
            # Restore original dependencies
            router.dependency_overrides = original_dependency

    def test_get_global_analysis_with_force_refresh(self, mock_analysis_service):
        """Test global analysis with force_refresh parameter."""
        client = TestClient(app)

        from analysis_router import router, get_analysis_service
        original_dependency = router.dependency_overrides.copy()

        async def override_analysis_service():
            return mock_analysis_service

        router.dependency_overrides[get_analysis_service] = override_analysis_service

        try:
            response = client.get("/api/analysis/global?force_refresh=true")

            assert response.status_code == 200
            data = response.json()

            assert 'analysis' in data
            assert data['cached'] is False
        finally:
            router.dependency_overrides = original_dependency


class TestAnalysisEndpointErrors:
    """Test error handling for analysis endpoints."""

    def test_global_analysis_prompt_not_found(self):
        """Test error when global analysis prompt doesn't exist."""
        client = TestClient(app)

        # Mock service that raises ValueError
        from analysis_router import router, get_analysis_service

        async def mock_generate_error(force_refresh=False):
            raise ValueError("Global analysis prompt not found")

        mock_service = MagicMock()
        mock_service.generate_global_analysis = mock_generate_error

        async def override_service():
            return mock_service

        original_dependency = router.dependency_overrides.copy()
        router.dependency_overrides[get_analysis_service] = override_service

        try:
            response = client.get("/api/analysis/global")

            # Should return 404 when prompt not found
            assert response.status_code == 404
            assert "not found" in response.json()['detail'].lower()
        finally:
            router.dependency_overrides = original_dependency

    def test_global_analysis_internal_error(self):
        """Test error handling for unexpected errors."""
        client = TestClient(app)

        from analysis_router import router, get_analysis_service

        async def mock_generate_error(force_refresh=False):
            raise Exception("Claude API timeout")

        mock_service = MagicMock()
        mock_service.generate_global_analysis = mock_generate_error

        async def override_service():
            return mock_service

        original_dependency = router.dependency_overrides.copy()
        router.dependency_overrides[get_analysis_service] = override_service

        try:
            response = client.get("/api/analysis/global")

            # Should return 500 for unexpected errors
            assert response.status_code == 500
            assert "Failed to generate analysis" in response.json()['detail']
        finally:
            router.dependency_overrides = original_dependency


class TestBulkAnalysisEndpoint:
    """Integration tests for /api/analysis/positions/bulk endpoint."""

    def test_bulk_analysis_success(self):
        """Test successful bulk analysis for multiple positions."""
        client = TestClient(app)

        from analysis_router import get_analysis_service

        async def mock_generate_position(symbol, force_refresh=False):
            return {
                'analysis': f'Analysis for {symbol}',
                'recommendation': 'HOLD' if symbol == 'BTC' else 'BUY_MORE',
                'generated_at': datetime.utcnow(),
                'tokens_used': 100,
                'cached': False
            }

        mock_service = MagicMock()
        mock_service.generate_position_analysis = mock_generate_position

        async def override_service():
            return mock_service

        original_dependency = app.dependency_overrides.copy()
        app.dependency_overrides[get_analysis_service] = override_service

        try:
            response = client.post(
                "/api/analysis/positions/bulk",
                json={"symbols": ["BTC", "ETH", "SOL"]}
            )

            assert response.status_code == 200
            data = response.json()

            assert 'analyses' in data
            assert 'total_tokens_used' in data
            assert len(data['analyses']) == 3
            assert 'BTC' in data['analyses']
            assert 'ETH' in data['analyses']
            assert 'SOL' in data['analyses']
            assert data['analyses']['BTC']['recommendation'] == 'HOLD'
            assert data['analyses']['ETH']['recommendation'] == 'BUY_MORE'
            assert data['total_tokens_used'] == 300  # 3 symbols × 100 tokens
        finally:
            app.dependency_overrides = original_dependency

    def test_bulk_analysis_max_limit(self):
        """Test bulk analysis enforces 10 position maximum."""
        client = TestClient(app)

        # Try to analyze 11 positions
        symbols = [f"SYM{i}" for i in range(11)]

        response = client.post(
            "/api/analysis/positions/bulk",
            json={"symbols": symbols}
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_bulk_analysis_empty_list(self):
        """Test bulk analysis with empty symbol list."""
        client = TestClient(app)

        response = client.post(
            "/api/analysis/positions/bulk",
            json={"symbols": []}
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_bulk_analysis_position_not_found(self):
        """Test bulk analysis when one position doesn't exist."""
        client = TestClient(app)

        from analysis_router import get_analysis_service

        async def mock_generate_with_error(symbol, force_refresh=False):
            if symbol == 'INVALID':
                raise ValueError(f"Position not found: {symbol}")
            return {
                'analysis': f'Analysis for {symbol}',
                'recommendation': 'HOLD',
                'generated_at': datetime.utcnow(),
                'tokens_used': 100,
                'cached': False
            }

        mock_service = MagicMock()
        mock_service.generate_position_analysis = mock_generate_with_error

        async def override_service():
            return mock_service

        original_dependency = app.dependency_overrides.copy()
        app.dependency_overrides[get_analysis_service] = override_service

        try:
            response = client.post(
                "/api/analysis/positions/bulk",
                json={"symbols": ["BTC", "INVALID"]}
            )

            # Bulk endpoint should return 404 if any position fails
            assert response.status_code == 404
        finally:
            app.dependency_overrides = original_dependency


@pytest.mark.skip(reason="Requires live Claude API key - run manually")
class TestAnalysisRouterIntegrationLive:
    """
    Live integration tests with real Claude API.

    These tests are skipped by default to avoid API costs.
    Run manually with: pytest -v -m skip tests/test_analysis_router.py::TestAnalysisRouterIntegrationLive
    """

    def test_live_global_analysis(self):
        """Test global analysis with live API (manual test only)."""
        # This would test with real database and Claude API
        # Skipped to avoid costs during automated testing
        pass
