import imaplib
from datetime import datetime
import time
import email as em
from sqlalchemy import func
from transformers import  pipeline
from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session
import regex as re
from .import models
from app.database import engine,get_db
import matplotlib.pyplot as plt

#---------------------------------------------------------------------------------------#

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

@app.get("/get_mail")
def get_mail(db:Session = Depends(get_db)):
    
    processed_emails = [email.body for email in db.query(models.sentiment_analysis).all()]
    #connecting mail server
    mail = imaplib.IMAP4_SSL('imap.gmail.com',port=993)
    #login email
    mail.login('performancemanagementsystem72@gmail.com','gyem xjdn yctk ihdf')
    #selecting inbox to read
    mail.select('Inbox')
    #define criteria
    date_since = (datetime.now().strftime('%d-%b-%Y'))
    print("")
    print(date_since)
    print("")
    
    typ, data = mail.search(None,'FROM "badrisrp3836@gmail.com"',f'(SINCE "{date_since}")')
    max_msg = 1
    msg_processed = 0
    
    # Predefined Categories
   
    categories = {
        
        "project closer":["project","closer","completed"],
        "customer issue resolving": ["customer","issue","resolved"],
        "technical excellence" : ["technical","excellence","innovative"],
        "communication effectiveness" :  ["communication","responsiveness","empathy","understanding","message","conciseness"],
        "goal achievement" : ["goal","work anniversary","milestone","congratulations","dedication"],
        "sales performance and targets":["sales","targets","metrics","bonus","incentives","commision","revenue"],
        "business development and networking":["business","networking","development","partnership","collaboration","market research","relationship building"]
        
    }
    
    
    with db:
     for num in data[0].split():
        if(msg_processed>= max_msg):
            break
        typ, msg_data = mail.fetch(num,'(RFC822)') 
        msg = em.message_from_bytes(msg_data[0][1])
        #Get sender,subject,body from mail
        sender = msg['From']
        subject = msg['Subject']
        body = msg['Body']
        if msg.is_multipart():
            for part in msg.get_payload():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload()
                elif part.get_content_type() == "text/html":
                    pass
        else:
            if msg.get_content_type() == 'text/plain':
                body = msg.get_payload()
            elif msg.get_content_type() == 'text/html':
                pass
        
        if body in processed_emails:
            print(f"Skipping email {body}")
            continue
            
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_list = re.findall(email_regex, body)

        
        # Print the sender subject and body
        
        print('From :',sender)
        print('Subject :',subject)
        print('Body :',body)
        print('Appreciation to : ' , email_list)
        
        email_category = []
        for category, keywords_list in categories.items():
            for keyword in keywords_list:
                if keyword in body:
                    email_category.append(category)
                    break
        
        print("Category : ",email_category)
        category_str = ",".join(email_category)
        
            
        sentiment_labels = {
            "LABEL_0":"NEGATIVE",
            "LABEL_1":"NEUTRAL",
            "LABEL_2":"POSITIVE"
        }
        
        sentiment_classifier = pipeline('sentiment-analysis',model='cardiffnlp/twitter-roberta-base-sentiment')
        sentiment = sentiment_classifier(body)
        sentiment_label = sentiment_labels[sentiment[0]['label']]
        print("Sentiment Analysis : ", sentiment_label)
        print("!*********************************************************************************************!")
        
        
        # Storing the analysis results to db
                
        db_sentiment = models.sentiment_analysis(sender=sender,subject=subject,body=body,appreciation = ",".join(email_list),
                                                    category = category_str ,sentiment=sentiment_label,score = sentiment[0]['score'])
        db.add(db_sentiment)
        db.commit()
        db.refresh(db_sentiment)
    
            
         # Storing the analysis count results to db
         
        distinct_emails = db.query(models.sentiment_analysis.appreciation.distinct()).all()

        for email in distinct_emails:
            email_id = email[0]
            
            positive_count = db.query(models.sentiment_analysis).filter(
                models.sentiment_analysis.appreciation == email_id,
                models.sentiment_analysis.sentiment == "POSITIVE"
            ).count()
            
            negative_subquery = db.query(
                func.count(models.sentiment_analysis.id)
            ).filter(
                models.sentiment_analysis.appreciation == email_id,
                models.sentiment_analysis.sentiment == "NEGATIVE"
            ).subquery()
            
            existing_email = db.query(models.sentiment_analysis_counts).filter_by(email_id=email_id).first()
            
            if existing_email:
                existing_email.positive_count = positive_count
                existing_email.negative_count = db.query(negative_subquery).scalar()
            else:
                new_email = models.sentiment_analysis_counts(
                    email_id=email_id,
                    positive_count=positive_count,
                    negative_count=db.query(negative_subquery).scalar()
                )
                db.add(new_email)
                
            db.commit()

    msg_processed += 1
    time.sleep(2)
    # Closing the mail
    mail.close()
    # logging out
    mail.logout()
    