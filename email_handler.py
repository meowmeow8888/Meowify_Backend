import smtplib
import ssl
from email.message import EmailMessage

my_email = "MeowifyMusicOfficial@gmail.com"
password = "ytvrnljefbuawvyd"


class Email_handler:
    @staticmethod
    def send_email(email, email_subject, email_body):
        em = EmailMessage()
        em["From"] = my_email
        em["To"] = email
        em["Subject"] = email_subject
        em.set_content(email_body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(my_email, password)
            smtp.send_message(em)

    @staticmethod
    def send_verification_code(email, method, code):
        Email_handler.send_email(email,
                                 f"{method} verification code",
                                 f"""Your two-factor {method} code
Code: {code}
Use this code to complete your {method}.""")


if __name__ == '__main__':
    Email_handler.send_verification_code("mosseriguy8@gmail.com", "Login", "190914")
