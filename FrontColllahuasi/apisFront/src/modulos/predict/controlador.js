const db = require("../../DB/mysql");

function getAllRXLVLRealDataByIP(elemIP, res) {
  return db.getAllRXLVLRealDataByIP(elemIP, res);
}

function getAllRXLVLPredDataByIP(elemIP, res) {
  return db.getAllRXLVLPredDataByIP(elemIP, res);
}

function getPredSNRDataByIP(ip, res) {
  return db.getPredSNRDataByIP(ip, res);
}

function getAllPredSNRData(res) {
  return db.getAllPredSNRData(res);
}

function getPredTabSNRDataByIP(elemIP, res) {
  return db.getPredTabSNRDataByIP(elemIP, res);
}

function getPredTableRXLVLData(elemIP, res) {
  return db.getPredTableRXLVLData(elemIP, res);
}

function getAllDataSNR(res) {
  return db.getAllDataSNR(res);
}

function getAllSNRDataByIP(res,ip) {
  return db.getAllSNRDataByIP(res,ip);
}

function getAllPredictRXLVLData(res) {
  return db.getAllPredictRXLVLData(res);
}

function getRealSNRDataByIP(res,ip) {
  return db.getRealSNRDataByIP(res,ip);
}


module.exports = {
  getAllRXLVLRealDataByIP,
  getAllRXLVLPredDataByIP,
  getPredTableRXLVLData,
  getAllPredSNRData,
  getPredTabSNRDataByIP,
  getPredSNRDataByIP,
  getAllDataSNR,
  getAllSNRDataByIP,
  getRealSNRDataByIP,
  getAllPredictRXLVLData,
};
