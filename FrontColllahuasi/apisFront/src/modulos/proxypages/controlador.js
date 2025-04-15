const db = require("../../DB/mysql");

function getTesteoData(res) {
  return db.getTesteoData(res);
}

function getAllData(res) {
  return db.getDataProxy(res);
}



module.exports = {
  getTesteoData,
  getAllData
};
