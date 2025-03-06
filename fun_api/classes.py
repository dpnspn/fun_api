import datetime
from typing import *


class User:
    def __init__(self, data: dict):
        '''
        A class for a user.
        '''
        self.data: dict = data
        self.id: int = data['id']
        self.name: str = data['displayName']
        self.gender: str = data['gender']
        self.avatar_image: str = data['avatar']
        self.age: int = data['age']
        self.links: Dict[str, str] = data['links']
        self.birthdate = datetime.datetime.fromisoformat(
            data['birthDate']
        ).astimezone(datetime.timezone.utc)