require("dotenv").config();

module.exports = {
  app: {
    port: process.env.PORT || 4000,
  },
  mysql: {
    host: process.env.MYSQL_HOST || "localhost",
    user: process.env.MYSQL_USER || "admin",
    password: process.env.MYSQL_PASS || "audio2023",
    database: process.env.MYSQL_DB || "smartlinkDB",
  },
};
