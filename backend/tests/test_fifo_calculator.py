# ABOUTME: Tests for FIFO cost basis calculator
# ABOUTME: Verifies FIFO algorithm for accurate tax reporting and P&L calculations

import pytest
from datetime import datetime
from decimal import Decimal
from fifo_calculator import FIFOCalculator, Lot, FIFOResult


class TestFIFOCalculator:
    """Test FIFO cost basis calculation"""

    def test_add_purchase_creates_lot(self):
        """Test that adding a purchase creates a new lot"""
        calc = FIFOCalculator()
        calc.add_purchase(
            ticker="AAPL",
            quantity=Decimal("100"),
            price=Decimal("150.00"),
            date=datetime(2024, 1, 1),
            transaction_id=1
        )

        lots = calc.get_lots("AAPL")
        assert len(lots) == 1
        assert lots[0].quantity == Decimal("100")
        assert lots[0].price == Decimal("150.00")

    def test_basic_fifo_sell(self):
        """Test basic FIFO sale - sell from oldest lot first"""
        calc = FIFOCalculator()

        # Buy 100 @ $10 on Jan 1
        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)

        # Buy 100 @ $15 on Feb 1
        calc.add_purchase("AAPL", Decimal("100"), Decimal("15.00"),
                         datetime(2024, 2, 1), 2)

        # Sell 150 @ $20 on Mar 1
        result = calc.process_sale("AAPL", Decimal("150"), Decimal("20.00"),
                                   datetime(2024, 3, 1), 3)

        # Should sell 100 @ $10 + 50 @ $15
        # Profit = (20-10)*100 + (20-15)*50 = 1000 + 250 = 1250
        assert result.realized_pnl == Decimal("1250.00")
        assert result.quantity_sold == Decimal("150")
        assert len(result.lots_sold) == 2

        # Check remaining lots
        remaining = calc.get_lots("AAPL")
        assert len(remaining) == 1
        assert remaining[0].quantity == Decimal("50")
        assert remaining[0].price == Decimal("15.00")

    def test_multiple_partial_sells(self):
        """Test multiple partial sales from same lot"""
        calc = FIFOCalculator()

        # Buy 100 @ $10
        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)

        # Sell 30 @ $12
        result1 = calc.process_sale("AAPL", Decimal("30"), Decimal("12.00"),
                                    datetime(2024, 2, 1), 2)
        assert result1.realized_pnl == Decimal("60.00")  # (12-10)*30

        # Sell 30 @ $14
        result2 = calc.process_sale("AAPL", Decimal("30"), Decimal("14.00"),
                                    datetime(2024, 3, 1), 3)
        assert result2.realized_pnl == Decimal("120.00")  # (14-10)*30

        # Sell 40 @ $16
        result3 = calc.process_sale("AAPL", Decimal("40"), Decimal("16.00"),
                                    datetime(2024, 4, 1), 4)
        assert result3.realized_pnl == Decimal("240.00")  # (16-10)*40

        # All from first lot, should be empty now
        remaining = calc.get_lots("AAPL")
        assert len(remaining) == 0

    def test_complete_position_closure(self):
        """Test selling entire position"""
        calc = FIFOCalculator()

        # Buy 50 @ $20
        calc.add_purchase("AAPL", Decimal("50"), Decimal("20.00"),
                         datetime(2024, 1, 1), 1)

        # Buy 50 @ $25
        calc.add_purchase("AAPL", Decimal("50"), Decimal("25.00"),
                         datetime(2024, 2, 1), 2)

        # Sell 100 @ $30
        result = calc.process_sale("AAPL", Decimal("100"), Decimal("30.00"),
                                   datetime(2024, 3, 1), 3)

        # Profit = (30-20)*50 + (30-25)*50 = 500 + 250 = 750
        assert result.realized_pnl == Decimal("750.00")
        assert result.quantity_sold == Decimal("100")

        # Position should be closed
        remaining = calc.get_lots("AAPL")
        assert len(remaining) == 0

    def test_sell_with_fee(self):
        """Test that fees are tracked but don't affect cost basis"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)

        result = calc.process_sale("AAPL", Decimal("100"), Decimal("15.00"),
                                   datetime(2024, 2, 1), 2,
                                   fee=Decimal("5.00"))

        # P&L before fees
        assert result.realized_pnl == Decimal("500.00")  # (15-10)*100
        # Fee should be tracked separately
        assert result.fee == Decimal("5.00")
        # Net P&L
        assert result.net_pnl == Decimal("495.00")

    def test_sell_more_than_available_raises_error(self):
        """Test that selling more shares than owned raises error"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)

        with pytest.raises(ValueError, match="Insufficient shares"):
            calc.process_sale("AAPL", Decimal("150"), Decimal("15.00"),
                            datetime(2024, 2, 1), 2)

    def test_sell_unknown_ticker_raises_error(self):
        """Test that selling unknown ticker raises error"""
        calc = FIFOCalculator()

        with pytest.raises(ValueError, match="No lots found"):
            calc.process_sale("AAPL", Decimal("100"), Decimal("15.00"),
                            datetime(2024, 1, 1), 1)

    def test_negative_pnl(self):
        """Test selling at a loss"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("20.00"),
                         datetime(2024, 1, 1), 1)

        result = calc.process_sale("AAPL", Decimal("100"), Decimal("15.00"),
                                   datetime(2024, 2, 1), 2)

        # Loss = (15-20)*100 = -500
        assert result.realized_pnl == Decimal("-500.00")
        assert result.quantity_sold == Decimal("100")

    def test_multiple_tickers(self):
        """Test FIFO tracking for multiple tickers independently"""
        calc = FIFOCalculator()

        # AAPL transactions
        calc.add_purchase("AAPL", Decimal("100"), Decimal("150.00"),
                         datetime(2024, 1, 1), 1)
        calc.add_purchase("AAPL", Decimal("50"), Decimal("160.00"),
                         datetime(2024, 2, 1), 2)

        # TSLA transactions
        calc.add_purchase("TSLA", Decimal("200"), Decimal("200.00"),
                         datetime(2024, 1, 15), 3)

        # Sell AAPL
        result_aapl = calc.process_sale("AAPL", Decimal("120"), Decimal("170.00"),
                                       datetime(2024, 3, 1), 4)

        # AAPL P&L = (170-150)*100 + (170-160)*20 = 2000 + 200 = 2200
        assert result_aapl.realized_pnl == Decimal("2200.00")

        # TSLA should be unchanged
        tsla_lots = calc.get_lots("TSLA")
        assert len(tsla_lots) == 1
        assert tsla_lots[0].quantity == Decimal("200")

    def test_get_total_cost_basis(self):
        """Test calculating total cost basis for remaining lots"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)
        calc.add_purchase("AAPL", Decimal("50"), Decimal("12.00"),
                         datetime(2024, 2, 1), 2)

        # Total cost = 100*10 + 50*12 = 1000 + 600 = 1600
        total_cost = calc.get_total_cost_basis("AAPL")
        assert total_cost == Decimal("1600.00")

    def test_get_average_cost_basis(self):
        """Test calculating weighted average cost basis"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)
        calc.add_purchase("AAPL", Decimal("50"), Decimal("16.00"),
                         datetime(2024, 2, 1), 2)

        # Avg cost = (100*10 + 50*16) / 150 = 1800 / 150 = 12.00
        avg_cost = calc.get_average_cost_basis("AAPL")
        assert avg_cost == Decimal("12.00")

    def test_get_total_quantity(self):
        """Test calculating total quantity remaining"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)
        calc.add_purchase("AAPL", Decimal("50"), Decimal("12.00"),
                         datetime(2024, 2, 1), 2)

        calc.process_sale("AAPL", Decimal("30"), Decimal("15.00"),
                         datetime(2024, 3, 1), 3)

        # Started with 150, sold 30, remaining 120
        total_qty = calc.get_total_quantity("AAPL")
        assert total_qty == Decimal("120")

    def test_audit_trail(self):
        """Test that FIFO maintains complete audit trail"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)

        result = calc.process_sale("AAPL", Decimal("50"), Decimal("15.00"),
                                   datetime(2024, 2, 1), 2)

        # Check audit trail details
        assert len(result.lots_sold) == 1
        sold_lot = result.lots_sold[0]
        assert sold_lot["quantity"] == Decimal("50")
        assert sold_lot["cost_basis"] == Decimal("10.00")
        assert sold_lot["proceeds"] == Decimal("15.00")
        assert sold_lot["pnl"] == Decimal("250.00")

    def test_decimal_precision(self):
        """Test that calculations maintain decimal precision"""
        calc = FIFOCalculator()

        # Use precise fractional quantities and prices
        calc.add_purchase("BTC", Decimal("0.12345678"), Decimal("50000.12345"),
                         datetime(2024, 1, 1), 1)

        result = calc.process_sale("BTC", Decimal("0.05"), Decimal("60000.00"),
                                   datetime(2024, 2, 1), 2)

        # Verify no floating point errors
        expected_pnl = (Decimal("60000.00") - Decimal("50000.12345")) * Decimal("0.05")
        assert result.realized_pnl == expected_pnl

    def test_chronological_order_not_enforced(self):
        """Test that transactions don't need to be added chronologically"""
        calc = FIFOCalculator()

        # Add out of order - FIFO should still work based on stored dates
        calc.add_purchase("AAPL", Decimal("100"), Decimal("15.00"),
                         datetime(2024, 2, 1), 2)
        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)

        # Sell should use oldest lot first (Jan 1 @ $10)
        result = calc.process_sale("AAPL", Decimal("50"), Decimal("20.00"),
                                   datetime(2024, 3, 1), 3)

        # P&L should be based on $10 cost (oldest), not $15
        assert result.realized_pnl == Decimal("500.00")  # (20-10)*50

    def test_get_all_tickers(self):
        """Test getting list of all tracked tickers"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)
        calc.add_purchase("TSLA", Decimal("50"), Decimal("200.00"),
                         datetime(2024, 1, 2), 2)
        calc.add_purchase("BTC", Decimal("1.5"), Decimal("50000.00"),
                         datetime(2024, 1, 3), 3)

        tickers = calc.get_all_tickers()
        assert len(tickers) == 3
        assert "AAPL" in tickers
        assert "TSLA" in tickers
        assert "BTC" in tickers

    def test_export_import_lots_json(self):
        """Test exporting and importing lots to/from JSON"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("150.00"),
                         datetime(2024, 1, 1), 1)
        calc.add_purchase("AAPL", Decimal("50"), Decimal("160.00"),
                         datetime(2024, 2, 1), 2)

        # Export to JSON
        lots_json = calc.export_lots_to_json("AAPL")
        assert len(lots_json) == 2
        assert lots_json[0]["quantity"] == "100"
        assert lots_json[0]["price"] == "150.00"

        # Clear and import
        calc.clear_ticker("AAPL")
        assert len(calc.get_lots("AAPL")) == 0

        calc.import_lots_from_json("AAPL", lots_json)
        imported_lots = calc.get_lots("AAPL")
        assert len(imported_lots) == 2
        assert imported_lots[0].quantity == Decimal("100")
        assert imported_lots[0].price == Decimal("150.00")

    def test_clear_all(self):
        """Test clearing all tickers"""
        calc = FIFOCalculator()

        calc.add_purchase("AAPL", Decimal("100"), Decimal("10.00"),
                         datetime(2024, 1, 1), 1)
        calc.add_purchase("TSLA", Decimal("50"), Decimal("200.00"),
                         datetime(2024, 1, 2), 2)

        calc.clear_all()
        assert len(calc.get_all_tickers()) == 0
        assert calc.get_total_quantity("AAPL") == Decimal("0")

    def test_fifo_result_properties(self):
        """Test FIFOResult calculated properties"""
        result = FIFOResult(
            ticker="AAPL",
            quantity_sold=Decimal("100"),
            sale_price=Decimal("150.00"),
            sale_date=datetime(2024, 3, 1),
            transaction_id=5,
            realized_pnl=Decimal("500.00"),
            fee=Decimal("10.00"),
            lots_sold=[
                {
                    "quantity": Decimal("100"),
                    "cost_basis": Decimal("145.00"),
                    "proceeds": Decimal("150.00"),
                    "pnl": Decimal("500.00"),
                    "purchase_date": "2024-01-01T00:00:00",
                    "transaction_id": 1
                }
            ]
        )

        assert result.net_pnl == Decimal("490.00")  # 500 - 10 fee
        assert result.total_proceeds == Decimal("15000.00")  # 100 * 150
        assert result.total_cost_basis == Decimal("14500.00")  # 100 * 145

    def test_lot_from_dict(self):
        """Test creating Lot from dictionary"""
        lot_dict = {
            "quantity": "100",
            "price": "150.00",
            "date": "2024-01-01T00:00:00",
            "transaction_id": 1
        }

        lot = Lot.from_dict(lot_dict)
        assert lot.quantity == Decimal("100")
        assert lot.price == Decimal("150.00")
        assert lot.transaction_id == 1
        assert lot.total_cost == Decimal("15000.00")

    def test_lot_to_dict(self):
        """Test converting Lot to dictionary"""
        lot = Lot(
            quantity=Decimal("100"),
            price=Decimal("150.00"),
            date=datetime(2024, 1, 1),
            transaction_id=1
        )

        lot_dict = lot.to_dict()
        assert lot_dict["quantity"] == "100"
        assert lot_dict["price"] == "150.00"
        assert lot_dict["transaction_id"] == 1

    def test_export_empty_ticker(self):
        """Test exporting lots for non-existent ticker"""
        calc = FIFOCalculator()
        lots_json = calc.export_lots_to_json("NONEXISTENT")
        assert lots_json == []
