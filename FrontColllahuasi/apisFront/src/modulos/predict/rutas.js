const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/rxlevel/getAllPredictRXLVLData", getAllPredictRXLVLData);
router.get("/rxlevel/getPredTableRXLVLData", getPredTableRXLVLData);
router.get("/rxlevel/getAllRXLVLPredDataByIP", getAllRXLVLPredDataByIP);
router.get("/rxlevel/getAllRXLVLRealDataByIP", getAllRXLVLRealDataByIP);

router.get("/snr/getAllPredSNRData", getAllPredSNRData);
router.get("/snr/getPredTabSNRDataByIP", getPredTabSNRDataByIP);
router.get("/snr/getPredSNRDataByIP", getPredSNRDataByIP);
router.get("/snr/getRealSNRDataByIP", getRealSNRDataByIP);
router.get("/snr/getAllDataSNR", getAllDataSNR);
// router.get("/snr/snralldata", allSNRData);
// router.get("/snr/snralldatabyip", allSNRDataByIP);


//Call in PREDICTSNRVIEW
async function getPredSNRDataByIP(req, res, next) {
  try {
    await controlador.getPredSNRDataByIP(req.query.ip, res);
  } catch (error) {
    next(error);
  }
}

//Call in PREDICTSNRVIEW
async function getRealSNRDataByIP(req, res, next) {
  try {
    await controlador.getRealSNRDataByIP(res,req.query.ip);
  } catch (error) {
    next(error);
  }
}

//Call in PREDICTSNRVIEW
async function getAllPredSNRData(req, res, next) {
  try {
    await controlador.getAllPredSNRData(res);
  } catch (error) {
    next(error);
  }
}

//Call in PREDICTSNRVIEW
async function getPredTabSNRDataByIP(req, res, next) {
  try {
    await controlador.getPredTabSNRDataByIP(req.query.ip, res);
  } catch (error) {
    next(error);
  }
}

//Call in SNRMAPSVIEW
async function getAllDataSNR(req, res, next) {
  try {
    await controlador.getAllDataSNR(res);
  } catch (error) {
    next(error);
  }
}

// async function allSNRDataByIP(req, res, next) {
//   try {
//     await controlador.getAllSNRDataByIP(res,req.query.ip);
//   } catch (error) {
//     next(error);
//   }
// }


//Call in PREDICTVIEW
async function getAllPredictRXLVLData(req, res, next) {
  try {
    await controlador.getAllPredictRXLVLData(res);
  } catch (error) {
    next(error);
  }
}

//Call in PREDICTVIEW
async function getPredTableRXLVLData(req, res, next) {
  try {
    await controlador.getPredTableRXLVLData(req.query.link, res);
  } catch (error) {
    next(error);
  }
}

//Call in PREDICTVIEW
async function getAllRXLVLPredDataByIP(req, res, next) {
  try {
    await controlador.getAllRXLVLPredDataByIP(req.query.link, res);
  } catch (error) {
    next(error);
  }
}

//Call in PREDICTVIEW
async function getAllRXLVLRealDataByIP(req, res, next) {
  try {
    await controlador.getAllRXLVLRealDataByIP(req.query.link, res);
  } catch (error) {
    next(error);
  }
}



module.exports = router;
