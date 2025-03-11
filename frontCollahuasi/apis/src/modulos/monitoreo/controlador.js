const db = require("../../DB/mysql");

function getTesteoData(res) {
  return db.getTesteoData(res);
}

function getAllDataGestor(res) {
  return db.getAllDataGestor(res);
}

function getAllDataIPS2(res) {
  return db.getAllDataIPS2(res);
}



module.exports = {
  getTesteoData,
  getAllDataGestor,
  getAllDataIPS2
};
