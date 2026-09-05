const express= require("express")
const app=express()

// Your AccountSID and Auth Token from console.twilio.com
const accountSid = process.env.TWILIO_ACCOUNT_SID;
const authToken = process.env.TWILIO_AUTH_TOKEN;

const client = require('twilio')(accountSid, authToken);

client.messages
  .create({
    body: 'From ClockCare.',
    to: '+91 9167123141', // Text your number
    from: '+17372508034', // From a valid Twilio number
  })
  .then((message) => console.log(message.sid));


app.listen(8080,()=>{
    console.log("Server running at 8080");
})