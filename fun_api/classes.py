import datetime
from typing import *
from dateutil import parser


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
        self.birthdate: datetime.datetime = datetime.datetime.fromisoformat(
            data['birthDate']
        ).astimezone(datetime.timezone.utc)


class Resource:
    def __init__(self, data: dict):
        '''
        A class for a resource in a project.
        '''
        self.data: dict = data

        self.id: int = data['id']
        self.name: str = data['name']
        self.url: str = data['url']
        self.type: str = data['resourceType']


class Project:
    def __init__(self, data: dict):
        '''
        A class for a project.
        '''
        self.data: dict = data

        self.id: int = data['id']
        self.author_id: int = data['studentId']
        self.title: str = data['title']
        self.description: str = data['desc']
        self.project_type: int = data['projectType']
        self.access_type: int = data['accessType']
        self.created_at: datetime.datetime = parser.isoparse(data['createdAt'])
        self.thumbnail: "str | None" = data.get('thumbnail', None)
        self.resources: List[Resource] = [
            Resource(i) for i in data['resources']
        ]
        self.url: "str | None" = data.get('url', None) # not available in previews
