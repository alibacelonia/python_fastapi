from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, BaseModel
from . import models
from .config import settings
from jinja2 import Environment, select_autoescape, PackageLoader


env = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


class EmailSchema(BaseModel):
    email: List[EmailStr]


class Email:
    def __init__(self, user: models.User, url: str = None, email: List[EmailStr] = None, otp_code: str = None, pet: models.Pet = None, coordinates: dict = None):
        self.name = user.firstname
        # self.name = user.firstname + " " + user.lastname
        self.sender = 'PetNFC <support@petnfc.com.au>'
        self.email = email
        self.url = url
        self.otp_code = otp_code
        self.pet = pet
        self.location = coordinates
        pass

    async def sendMail(self, subject, template, **kwargs):
        # Define the config
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.EMAIL_USERNAME,
            MAIL_PASSWORD=settings.EMAIL_PASSWORD,
            MAIL_FROM=settings.EMAIL_FROM,
            MAIL_FROM_NAME=f'PetNFC <{settings.EMAIL_FROM}>',
            MAIL_PORT=settings.EMAIL_PORT,
            MAIL_SERVER=settings.EMAIL_HOST,
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        # Generate the HTML template base on the template name
        template = env.get_template(f'{template}.html')

        html = template.render(**kwargs)

        # Define the message options
        message = MessageSchema(
            subject=subject,
            recipients=self.email,
            body=html,
            subtype="html"
        )

        # Send the email
        fm = FastMail(conf)
        await fm.send_message(message)

    async def sendVerificationCode(self):
        
        await self.sendMail(subject='Your verification code (Valid for 5min)', template='verification', url=self.url, first_name=self.name)
        
    async def sendOTP(self):
        await self.sendMail(subject='One-Time Password Code', template='otp', first_name=self.name, otp_code=self.otp_code)
        
    async def sendResetLink(self):
        await self.sendMail(subject='Password Reset Request', template='reset_password', url=self.url, first_name=self.name)
        
    async def sendScanNotificationEmail(self):
        await self.sendMail(subject='Pet Tag Scanned Notification', template='scan_notification', url=self.url, first_name=self.name, pet_name=self.pet.name, latitude=self.location["latitude"], longitude=self.location["longitude"])
