from abc import ABC, abstractmethod


class ClientRepository(ABC):

    @abstractmethod
    def add(self, client):
        pass

    @abstractmethod
    def get_by_id(self, client_id):
        pass


class MembershipRepository(ABC):

    @abstractmethod
    def add(self, membership):
        pass

    @abstractmethod
    def get_active(self, client_id):
        pass


class WorkoutRepository(ABC):

    @abstractmethod
    def add(self, workout):
        pass

    @abstractmethod
    def get_by_id(self, workout_id):
        pass


class BookingRepository(ABC):

    @abstractmethod
    def add(self, booking):
        pass

    @abstractmethod
    def count_for_workout(self, workout_id):
        pass