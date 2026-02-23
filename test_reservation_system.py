
"""
Unit tests for Reservation System (unittest).

Cubre creación, modificación, consultas, reservas y cancelaciones,
además de 5 casos negativos requeridos.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reservation_system import (
    DataStore,
    ReservationSystem,
    Hotel,
    Customer,
    Reservation,
)


class ReservationSystemTests(unittest.TestCase):
    """End-to-end tests sobre un directorio temporal."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.store = DataStore(self.base)
        self.svc = ReservationSystem(self.store)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    # --------- Helpers ---------
    def _sample_hotel_customer(self) -> tuple[Hotel, Customer]:
        h = self.svc.create_hotel("Azure Inn", "Monterrey", 5)
        c = self.svc.create_customer("Isaac Reyes", "isaac@example.com")
        return h, c

    # --------- Pruebas positivas ---------
    def test_create_and_info_hotel_customer(self) -> None:
        h, c = self._sample_hotel_customer()
        info_h = self.svc.hotel_info(h.hotel_id)
        info_c = self.svc.customer_info(c.customer_id)
        self.assertIn("Azure Inn", info_h or "")
        self.assertIn("Isaac Reyes", info_c or "")

    def test_reserve_and_cancel(self) -> None:
        h, c = self._sample_hotel_customer()
        res = self.svc.create_reservation(h.hotel_id, c.customer_id, 2)
        self.assertIsInstance(res, Reservation)
        ok = self.svc.cancel_reservation(res.reservation_id)
        self.assertTrue(ok)

    def test_modify_entities(self) -> None:
        h, c = self._sample_hotel_customer()
        ok_h = self.svc.modify_hotel(h.hotel_id, name="Azure Suites")
        ok_c = self.svc.modify_customer(c.customer_id, email="new@mail.com")
        self.assertTrue(ok_h)
        self.assertTrue(ok_c)
        info_h = self.svc.hotel_info(h.hotel_id)
        info_c = self.svc.customer_info(c.customer_id)
        self.assertIn("Azure Suites", info_h or "")
        self.assertIn("new@mail.com", info_c or "")

    # --------- Casos NEGATIVOS (5) ---------

    def test_negative_overbooking(self) -> None:
        """(1) Reservar más cuartos de los disponibles."""
        h, c = self._sample_hotel_customer()
        res1 = self.svc.create_reservation(h.hotel_id, c.customer_id, 5)
        self.assertIsNotNone(res1)  # exactamente los 5
        res2 = self.svc.create_reservation(h.hotel_id, c.customer_id, 1)
        self.assertIsNone(res2)  # no hay más disponibilidad

    def test_negative_unknown_customer(self) -> None:
        """(2) Reservar con cliente inexistente."""
        h, _ = self._sample_hotel_customer()
        res = self.svc.create_reservation(h.hotel_id, "no-such-id", 1)
        self.assertIsNone(res)

    def test_negative_unknown_hotel(self) -> None:
        """(3) Reservar con hotel inexistente."""
        _, c = self._sample_hotel_customer()
        res = self.svc.create_reservation("no-such-id", c.customer_id, 1)
        self.assertIsNone(res)

    def test_negative_delete_hotel_with_active_reservations(self) -> None:
        """(4) Intentar borrar hotel con reservas activas."""
        h, c = self._sample_hotel_customer()
        self.svc.create_reservation(h.hotel_id, c.customer_id, 1)
        ok = self.svc.delete_hotel(h.hotel_id)
        self.assertFalse(ok)

    def test_negative_corrupted_json(self) -> None:
        """(5) Cargar JSON corrupto (debe loggear y continuar)."""
        hotels_path = self.base / "hotels.json"
        hotels_path.write_text("{ invalid json", encoding="utf-8")
        hotels = self.store.load_hotels()
        self.assertEqual(hotels, [])

    # --------- Más validaciones de negocio ---------

    def test_delete_customer_with_active_reservation(self) -> None:
        h, c = self._sample_hotel_customer()
        self.svc.create_reservation(h.hotel_id, c.customer_id, 1)
        ok = self.svc.delete_customer(c.customer_id)
        self.assertFalse(ok)

    def test_cancel_nonexistent_reservation(self) -> None:
        ok = self.svc.cancel_reservation("no-such-id")
        self.assertFalse(ok)

    def test_total_and_available_rooms(self) -> None:
        h, c = self._sample_hotel_customer()
        self.svc.create_reservation(h.hotel_id, c.customer_id, 2)
        info = self.svc.hotel_info(h.hotel_id) or ""
        self.assertIn("available: 3", info)


if __name__ == "__main__":
    unittest.main()
