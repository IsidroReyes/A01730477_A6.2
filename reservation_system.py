
"""
Reservation System: Hotels, Customers, Reservations.

- Classes: Hotel, Customer, Reservation.
- Persistence: JSON files per entity.
- Methods: create, delete, display, modify; reserve and cancel.
- Error handling: logs invalid data and continues.
- Style: PEP 8, lines <=79, flake8/pylint friendly.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# =========================
#  Domain Models
# =========================


@dataclass(frozen=True)
class Hotel:
    """Hotel model for persistence and business operations."""

    hotel_id: str
    name: str
    city: str
    total_rooms: int

    def to_dict(self) -> Dict[str, object]:
        """Return this hotel as a plain serializable dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, object]) -> Optional['Hotel']:
        """Create a :class:`Hotel` from *data* or return ``None`` on error."""
        try:
            return Hotel(
                hotel_id=str(data['hotel_id']),
                name=str(data['name']),
                city=str(data['city']),
                total_rooms=int(data['total_rooms']),
            )
        except (KeyError, TypeError, ValueError) as exc:
            logging.error('Invalid hotel record: %r', exc)
            return None


@dataclass(frozen=True)
class Customer:
    """Customer model storing basic contact data."""

    customer_id: str
    name: str
    email: str

    def to_dict(self) -> Dict[str, object]:
        """Return this customer as a serializable dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, object]) -> Optional['Customer']:
        """Create a :class:`Customer` from *data* or return ``None`` on error.
        """
        try:
            return Customer(
                customer_id=str(data['customer_id']),
                name=str(data['name']),
                email=str(data['email']),
            )
        except (KeyError, TypeError, ValueError) as exc:
            logging.error('Invalid customer record: %r', exc)
            return None


@dataclass(frozen=True)
class Reservation:
    """Reservation model linking a customer with a hotel."""

    reservation_id: str
    hotel_id: str
    customer_id: str
    rooms: int
    status: str = 'active'

    def to_dict(self) -> Dict[str, object]:
        """Return this reservation as a serializable dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, object]) -> Optional['Reservation']:
        """Create a :class:`Reservation` from *data* or return ``None``.
        """
        try:
            return Reservation(
                reservation_id=str(data['reservation_id']),
                hotel_id=str(data['hotel_id']),
                customer_id=str(data['customer_id']),
                rooms=int(data['rooms']),
                status=str(data.get('status', 'active')),
            )
        except (KeyError, TypeError, ValueError) as exc:
            logging.error('Invalid reservation record: %r', exc)
            return None


# =========================
#  Persistence
# =========================


class DataStore:
    """JSON-based storage for Hotels, Customers and Reservations."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize the store under *base_dir* and ensure it exists."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._paths = {
            'hotels': self.base_dir / 'hotels.json',
            'customers': self.base_dir / 'customers.json',
            'reservations': self.base_dir / 'reservations.json',
        }

    def _load_raw(self, key: str) -> List[dict]:
        """Load a JSON array from the file for *key*; return [] on error."""
        path = self._paths[key]
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(data, list):
                return data
            logging.error('File %s must contain a JSON array.', path.name)
            return []
        except json.JSONDecodeError as exc:
            logging.error(
                'Invalid JSON in %s (line %d, col %d). Continuing...',
                path.name,
                exc.lineno,
                exc.colno,
            )
            return []

    def _save_raw(self, key: str, rows: List[dict]) -> None:
        """Write *rows* as JSON array to the file for *key*."""
        path = self._paths[key]
        text = json.dumps(rows, ensure_ascii=False, indent=2) + ''
        path.write_text(text, encoding='utf-8')

    def load_hotels(self) -> List[Hotel]:
        """Return all hotels, skipping invalid entries."""
        hotels: List[Hotel] = []
        for row in self._load_raw('hotels'):
            obj = Hotel.from_dict(row)
            if obj:
                hotels.append(obj)
        return hotels

    def save_hotels(self, hotels: List[Hotel]) -> None:
        """Persist *hotels* to disk."""
        self._save_raw('hotels', [h.to_dict() for h in hotels])

    def load_customers(self) -> List[Customer]:
        """Return all customers, skipping invalid entries."""
        customers: List[Customer] = []
        for row in self._load_raw('customers'):
            obj = Customer.from_dict(row)
            if obj:
                customers.append(obj)
        return customers

    def save_customers(self, customers: List[Customer]) -> None:
        """Persist *customers* to disk."""
        self._save_raw('customers', [c.to_dict() for c in customers])

    def load_reservations(self) -> List[Reservation]:
        """Return all reservations, skipping invalid entries."""
        res: List[Reservation] = []
        for row in self._load_raw('reservations'):
            obj = Reservation.from_dict(row)
            if obj:
                res.append(obj)
        return res

    def save_reservations(self, reservations: List[Reservation]) -> None:
        """Persist *reservations* to disk."""
        self._save_raw('reservations', [r.to_dict() for r in reservations])


# =========================
#  Services / Use cases
# =========================


class ReservationSystem:
    """Application services for the reservation domain."""

    def __init__(self, store: DataStore) -> None:
        """Bind the service to a :class:`DataStore` instance."""
        self.store = store

    Aggregate = Tuple[List[Hotel], List[Customer], List[Reservation]]

    def _load_all(self) -> Aggregate:
        """Load all entity lists from storage and return a tuple."""
        return (
            self.store.load_hotels(),
            self.store.load_customers(),
            self.store.load_reservations(),
        )

    def _save_all(
        self,
        hotels: List[Hotel],
        customers: List[Customer],
        reservations: List[Reservation],
    ) -> None:
        """Persist the three entity lists to storage in one step."""
        self.store.save_hotels(hotels)
        self.store.save_customers(customers)
        self.store.save_reservations(reservations)

    # ---- Hotels ----
    def create_hotel(self, name: str, city: str, total_rooms: int) -> Hotel:
        """Create a hotel and persist it; return the new hotel."""
        if total_rooms <= 0:
            raise ValueError('total_rooms must be > 0')
        hotels, customers, reservations = self._load_all()
        new_hotel = Hotel(
            hotel_id=str(uuid.uuid4()),
            name=name.strip(),
            city=city.strip(),
            total_rooms=int(total_rooms),
        )
        hotels.append(new_hotel)
        self._save_all(hotels, customers, reservations)
        return new_hotel

    def delete_hotel(self, hotel_id: str) -> bool:
        """Delete a hotel if no active reservations reference it."""
        hotels, customers, reservations = self._load_all()
        if any(
            r for r in reservations
            if r.hotel_id == hotel_id and r.status == 'active'
        ):
            logging.error(
                'Cannot delete hotel %s: active reservations exist.', hotel_id
            )
            return False
        new_hotels = [h for h in hotels if h.hotel_id != hotel_id]
        if len(new_hotels) == len(hotels):
            logging.error('Hotel %s not found.', hotel_id)
            return False
        self._save_all(new_hotels, customers, reservations)
        return True

    def get_hotel(self, hotel_id: str) -> Optional[Hotel]:
        """Return the hotel by *hotel_id* or ``None`` if missing."""
        hotels = self.store.load_hotels()
        for h in hotels:
            if h.hotel_id == hotel_id:
                return h
        logging.error('Hotel %s not found.', hotel_id)
        return None

    def modify_hotel(
        self,
        hotel_id: str,
        *,
        name: Optional[str] = None,
        city: Optional[str] = None,
        total_rooms: Optional[int] = None,
    ) -> bool:
        """Update hotel fields if found; return ``True`` on success."""
        hotels, customers, reservations = self._load_all()
        found = False
        new_hotels: List[Hotel] = []
        for h in hotels:
            if h.hotel_id != hotel_id:
                new_hotels.append(h)
                continue
            found = True
            new_rooms = h.total_rooms if total_rooms is None else total_rooms
            if new_rooms <= 0:
                logging.error('total_rooms must be > 0')
                return False
            updated = Hotel(
                hotel_id=h.hotel_id,
                name=h.name if name is None else name.strip(),
                city=h.city if city is None else city.strip(),
                total_rooms=int(new_rooms),
            )
            new_hotels.append(updated)
        if not found:
            logging.error('Hotel %s not found.', hotel_id)
            return False
        self._save_all(new_hotels, customers, reservations)
        return True

    # ---- Customers ----
    def create_customer(self, name: str, email: str) -> Customer:
        """Create a customer and persist it; return the new customer."""
        hotels, customers, reservations = self._load_all()
        new_customer = Customer(
            customer_id=str(uuid.uuid4()),
            name=name.strip(),
            email=email.strip(),
        )
        customers.append(new_customer)
        self._save_all(hotels, customers, reservations)
        return new_customer

    def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer if no active reservations reference it."""
        hotels, customers, reservations = self._load_all()
        if any(
            r for r in reservations
            if r.customer_id == customer_id and r.status == 'active'
        ):
            logging.error(
                'Cannot delete customer %s: active reservations exist.',
                customer_id,
            )
            return False
        new_customers = [c for c in customers if c.customer_id != customer_id]
        if len(new_customers) == len(customers):
            logging.error('Customer %s not found.', customer_id)
            return False
        self._save_all(hotels, new_customers, reservations)
        return True

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Return the customer by *customer_id* or ``None`` if missing."""
        customers = self.store.load_customers()
        for c in customers:
            if c.customer_id == customer_id:
                return c
        logging.error('Customer %s not found.', customer_id)
        return None

    def modify_customer(
        self,
        customer_id: str,
        *,
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> bool:
        """Update customer fields if found; return ``True`` on success."""
        hotels, customers, reservations = self._load_all()
        found = False
        new_customers: List[Customer] = []
        for c in customers:
            if c.customer_id != customer_id:
                new_customers.append(c)
                continue
            found = True
            updated = Customer(
                customer_id=c.customer_id,
                name=c.name if name is None else name.strip(),
                email=c.email if email is None else email.strip(),
            )
            new_customers.append(updated)
        if not found:
            logging.error('Customer %s not found.', customer_id)
            return False
        self._save_all(hotels, new_customers, reservations)
        return True

    # ---- Reservations ----
    @staticmethod
    def _hotel_available_rooms(
        hotel: Hotel,
        reservations: List[Reservation],
    ) -> int:
        """Compute remaining rooms for *hotel* among active reservations."""
        used = sum(
            r.rooms for r in reservations
            if r.hotel_id == hotel.hotel_id and r.status == 'active'
        )
        return hotel.total_rooms - used

    def create_reservation(
        self,
        hotel_id: str,
        customer_id: str,
        rooms: int,
    ) -> Optional[Reservation]:
        """Create a reservation if capacity and references are valid."""
        if rooms <= 0:
            logging.error('rooms must be > 0')
            return None

        hotels, customers, reservations = self._load_all()
        hotel = next((h for h in hotels if h.hotel_id == hotel_id), None)
        if hotel is None:
            logging.error('Hotel %s not found.', hotel_id)
            return None
        customer = next(
            (c for c in customers if c.customer_id == customer_id), None
        )
        if customer is None:
            logging.error('Customer %s not found.', customer_id)
            return None

        available = self._hotel_available_rooms(hotel, reservations)
        if rooms > available:
            logging.error(
                'Not enough rooms: requested=%d available=%d',
                rooms,
                available,
            )
            return None

        res = Reservation(
            reservation_id=str(uuid.uuid4()),
            hotel_id=hotel_id,
            customer_id=customer_id,
            rooms=rooms,
            status='active',
        )
        reservations.append(res)
        self._save_all(hotels, customers, reservations)
        return res

    def cancel_reservation(self, reservation_id: str) -> bool:
        """Cancel a reservation if it exists; idempotent on repeated calls."""
        hotels, customers, reservations = self._load_all()
        updated: List[Reservation] = []
        found = False
        for r in reservations:
            if r.reservation_id == reservation_id:
                found = True
                if r.status == 'cancelled':
                    logging.error('Reservation %s already cancelled.',
                                  reservation_id)
                    updated.append(r)
                    continue
                updated.append(
                    Reservation(
                        reservation_id=r.reservation_id,
                        hotel_id=r.hotel_id,
                        customer_id=r.customer_id,
                        rooms=r.rooms,
                        status='cancelled',
                    )
                )
            else:
                updated.append(r)
        if not found:
            logging.error('Reservation %s not found.', reservation_id)
            return False
        self._save_all(hotels, customers, updated)
        return True

    def hotel_info(self, hotel_id: str) -> Optional[str]:
        """Return a short summary string for the hotel state."""
        hotels, _, reservations = self._load_all()
        hotel = next((h for h in hotels if h.hotel_id == hotel_id), None)
        if hotel is None:
            logging.error('Hotel %s not found.', hotel_id)
            return None
        available = self._hotel_available_rooms(hotel, reservations)
        return (
            f"Hotel '{hotel.name}' in {hotel.city} — total: "
            f"{hotel.total_rooms}, available: {available}"
        )

    def customer_info(self, customer_id: str) -> Optional[str]:
        """Return a short summary string for the customer state."""
        customers = self.store.load_customers()
        customer = next((c for c in customers if c.customer_id == customer_id),
                        None)
        if customer is None:
            logging.error('Customer %s not found.', customer_id)
            return None
        return f"Customer '{customer.name}' <{customer.email}>"
