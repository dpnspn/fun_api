import datetime
import json
import os
from typing import *
import requests
import base64
from .classes import *
from dateutil import parser
from .exceptions import *


class Credentials:
    def __init__(self, filename: "str | None" = '.credentials'):
        '''
        A class for storing the credentials of the user.

        Set filename to None to remove file interaction.
        '''
        self.filename: "str | None" = filename


    @property
    def is_access_expired(self) -> bool:
        '''
        Returns True if the access token is expired.
        '''
        return self.access_expire < datetime.datetime.now(
            datetime.timezone.utc
        ).timestamp()


    @property
    def is_refresh_expired(self) -> bool:
        '''
        Returns True if the refresh token is expired.
        '''
        return self.refresh_expire < datetime.datetime.now(
            datetime.timezone.utc
        ).timestamp()

    
    def decode_token(self) -> dict:
        '''
        Returns the decoded info gotten from the token.
        '''
        data = self.access_token.split('.')[1]
        return json.loads(base64.b64decode(data+'=='))


    def load(self) -> bool:
        '''
        Loads the credentials from the file.
        '''
        if self.filename is None:
            return False
        
        if not os.path.exists(self.filename):
            return False
        
        with open(self.filename, 'r') as f:
            self.access_token: str = f.readline().strip()
            self.refresh_token: str = f.readline().strip()
            self.access_expire: float = float(f.readline().strip())
            self.refresh_expire: float = float(f.readline().strip())

        return True
    

    def save(self):
        '''
        Saves current credentials to the file.
        '''
        if self.filename is None:
            return
        
        with open(self.filename, 'w') as f:
            data = f'{self.access_token}\n{self.refresh_token}\n'\
                f'{self.access_expire}\n{self.refresh_expire}'
            f.write(data)
    


class Session:
    def __init__(self,
        credentials_filename: "str | None" = '.credentials',
        domain:str = 'api.funcode.school'
    ):
        '''
        A class for working with the API.
        '''
        self.domain: str = domain
        self.session = requests.Session()
        self.credentials_filename: "str | None" = credentials_filename
        self.credentials: "Credentials | None" = None
        self.user_id: "int | None" = None


    def set_credentials(self, data: dict):
        '''
        Gets credentials from a json and saves them for use in this session.
        '''
        self.credentials = Credentials(self.credentials_filename)

        self.credentials.access_token = data['token']
        self.credentials.refresh_token = data['refresh']
        self.credentials.access_expire = parser.isoparse(
            data['authExpire']
        ).timestamp()
        self.credentials.refresh_expire = parser.isoparse(
            data['refreshExpire']
        ).timestamp()

        self.credentials.save()

        # user data
        credentials_data = self.credentials.decode_token()
        self.user_id = credentials_data['user_id']


    def check_credentials(self):
        '''
        Checks if the credentials are valid.

        If not, raises an error.
        '''
        if self.credentials is None:
            raise FunapiException('Not logged in!')
        
        if self.credentials.is_refresh_expired:
            raise FunapiException('Invalid credentials')

        if self.credentials.is_access_expired:
            # todo add this refresh thingie
            # todo idfk what the refresh API endpoint is,
            # todo but it's definitely not /auth/refresh
            # todo since it 403's on me and asks for login and password.
            raise FunapiException('Access token expired, refresh API not implemented yet')
            self.refresh()


    def get(self, *args, **kwargs):
        '''
        Sends a GET request to the API.
        '''
        self.check_credentials()
        
        return self.session.get(
            *args,
            headers={'Authorization': f'Bearer {self.credentials.access_token}'},
            **kwargs
        )


    def post(self, *args, **kwargs):
        '''
        Sends a POST request to the API.
        '''
        self.check_credentials()
        
        return self.session.post(
            *args,
            headers={'Authorization': f'Bearer {self.credentials.access_token}'},
            **kwargs
        )

    
    def password_login(self, username:str, password:str):
        '''
        Logs the user in with the username and password.
        '''
        if self.credentials != None:
            raise FunapiException('Already logged in!')
        
        self.username: str = username
        self.password: str = password
        
        data = self.session.post(
            f'https://{self.domain}/api/auth/login/',
            json={'login':username, 'password':password, 'role':'student'}
        )

        if data.status_code == 403:
            raise FunapiException('Invalid username or password')
        
        self.set_credentials(data.json())


    def login(self, username:str, password:str):
        '''
        If there are no credentials, logs the user in with the
        username and password.

        If there are, loads them from file.
        '''
        # todo normal logger perhaps?
        if self.credentials_filename == None:
            print('No credentials file provided, logging in with password...')
            self.password_login(username, password)
            return
        
        if not os.path.exists(self.credentials_filename):
            print('No credentials file found, logging in with password...')
            self.password_login(username, password)
            return
        
        print('Loading data from credentials file...')
        self.credentials = Credentials(self.credentials_filename)
        self.credentials.load()
        credentials_data = self.credentials.decode_token()
        self.user_id = credentials_data['user_id']


    def login_from_credentials_file(self):
        '''
        Loads credentials from the file.
        '''
        if self.credentials_filename == None:
            raise FunapiException('Credentials file not set')
        
        if not os.path.exists(self.credentials_filename):
            raise FunapiException('Credentials file not found')
        
        print('Loading data from credentials file...')
        self.credentials = Credentials(self.credentials_filename)
        self.credentials.load()
        credentials_data = self.credentials.decode_token()
        self.user_id = credentials_data['user_id']


    def get_user(self, user_id: int) -> User:
        '''
        Gets a user by their ID.
        '''
        data = self.get(
            f'https://{self.domain}/api/student/profile/{user_id}'
        )
        if data.status_code == 404:
            raise FunapiException('User not found')

        return User(data.json()['data'])
    

    def get_me(self) -> User:
        '''
        Shorthand for Session.get_user(Session.user_id).
        '''
        return self.get_user(self.user_id)


    def get_projects(self, user_id: int = None) -> List[Project]:
        '''
        Gets a list of projects of the user.

        Use None to get your own projects.

        If user not found, returns an empty list. All questions
        to the API's creator.
        '''
        if user_id == None:
            user_id = self.user_id
        
        data = self.get(
            f'https://{self.domain}/api/student/{user_id}/project'
        )

        return [Project(i) for i in data.json()['data']]


    def get_project(self, id: int) -> "Project | None":
        '''
        Get a project by its ID.

        If project not found, return None.
        '''
        data = self.get(
            f'https://{self.domain}/api/student/{self.user_id}/project/{id}'
        )
        try:
            project = Project(data.json()['data'])
        except:
            return None
        else:
            return project
    
    
    def new_project(self,
        project_type: int,
        title: int
    ) -> int:
        '''
        Creates a new project.

        Returns the project ID.
        '''
        if project_type not in range(0,10):
            raise FunapiException('Invalid project type')
        
        data = self.post(
            f'https://{self.domain}/api/student/{self.user_id}/project',
            json={
                'title': title,
                'projectType': project_type,
                'studentId': self.user_id
            }
        )
        if data.status_code != 201:
            raise FunapiException('Failed to create project')
        
        return int(data.text)
    
    
    def edit_project(self,
        id: int,
        title: int = None,
        description: str = None,
        access_type: int = None
    ) -> int:
        '''
        Edits an existing project.
        '''
        if title == None and description == None and access_type == None:
            raise FunapiException('Specify data to edit!')
        
        if access_type not in [None,0,1,9]:
            raise FunapiException('Invalid access type')

        # fetching old project data because shit breaks if we just pass in the new data
        data = self.get_project(id)

        if data == None:
            raise FunapiException('Project not found')
        
        data = data.data

        if title:
            data['title'] = title
        if description:
            data['desc'] = description
        if access_type:
            data['accessType'] = access_type

        data = self.post(
            f'https://{self.domain}/api/student/{self.user_id}/project/{id}',
            json=data
        )
        if data.status_code != 201:
            raise FunapiException('Failed to edit project')
        
    
    # def delete_project(self, project_id: int):
    #     '''
    #     Deletes a project.
    #
    #     This endpoint is not implemented on the server yet.
    #     '''
    #     data = self.post(
    #         f'https://{self.domain}/api/student/{self.user_id}/project/{project_id}/delete/'
    #     )