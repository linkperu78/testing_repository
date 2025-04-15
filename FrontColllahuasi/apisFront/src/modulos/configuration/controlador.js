const db = require("../../DB/mysql");

function getTesteoData(res) {
  return db.getTesteoData(res);
}

function getAllData(res) {
  return db.getAllData(res);
}



module.exports = {
  getTesteoData,
  getAllData
};
