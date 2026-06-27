from src.repositories import (
    ClientRepository,
    MembershipRepository,
    WorkoutRepository,
    BookingRepository
)


class InMemoryClientRepository(ClientRepository):

    def __init__(self):
        self.clients = {}

    def add(self, client):
        self.clients[client.id] = client

    def get_by_id(self, client_id):
        return self.clients.get(client_id)


class InMemoryMembershipRepository(MembershipRepository):

    def __init__(self):
        self.memberships = {}

    def add(self, membership):
        self.memberships[membership.client_id] = membership

    def get_active(self, client_id):
        return self.memberships.get(client_id)


class InMemoryWorkoutRepository(WorkoutRepository):

    def __init__(self):
        self.workouts = {}

    def add(self, workout):
        self.workouts[workout.id] = workout

    def get_by_id(self, workout_id):
        return self.workouts.get(workout_id)


class InMemoryBookingRepository(BookingRepository):

    def __init__(self):
        self.bookings = []

    def add(self, booking):
        self.bookings.append(booking)

    def count_for_workout(self, workout_id):
        return len([
            booking
            for booking in self.bookings
            if booking.workout_id == workout_id
        ])