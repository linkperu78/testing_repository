const nodemailer = require("nodemailer");
const transporter = nodemailer.createTransport({
  host: "smtp.gmail.com",
  port: 465,
  secure: true,
  auth: {
    user: "marancibia@hcglsa.com",
    pass: "sofqcxzbgnesttro",
  },
});

module.exports = transporter;
