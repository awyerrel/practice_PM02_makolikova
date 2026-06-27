def cancel_booking(bookings: dict, booking_id: int):
    if booking_id not in bookings:
        raise ValueError("Booking not found")

    bookings[booking_id]["status"] = "cancelled"
    return bookings[booking_id]


def get_active_bookings(bookings: list):
    return [b for b in bookings if b.get("status") != "cancelled"]