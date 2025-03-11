const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getAllLatLngPMPSM", getAllLatLngPMPSM);
router.get("/getAllLatLngPMPAP", getAllLatLngPMPAP);
router.get("/getAllPolylines", getAllPolylines);
router.get("/getAllLatLngRAJANT", getAllLatLngRAJANT);
router.get("/getAllLatLngANY", getAllLatLngANY);
router.get("/getAllLatLngGPSTEST", getAllLatLngGPSTEST);
router.get("/getCoverage", getCoverage);
router.get("/getAllHaulTrucks", getAllHaulTrucks);
router.get("/getAllHaulTrucksDrive", getAllHaulTrucksDrive);
router.get("/getPositionHaulTrucks", getPositionHaulTrucks);
router.get("/getPositionDrives", getPositionDrives);
router.get("/getPositionDrivesRajant", getPositionDrivesRajant);
// router.get("/coblatency", getMapCoberturaLatency);
// router.get("/coblatlng", getMapCoberturaLatLng);

//Call in HEATMAPCARD
//Call in NETWORKCHART
//Call in MAPSVIEW
async function getAllLatLngPMPSM(req, res, next) {
  try {
    await controlador.getAllLatLngPMPSM(res);
  } catch (error) {
    next(error);
  }
}

async function getAllLatLngANY(req, res, next) {
  try {
    const items = await controlador.getAllLatLngANY();
    respuesta.success(req, res, items, 200);
  } catch (error) {
    next(error);
  }
}

async function getAllLatLngGPSTEST(req, res, next) {
  try {
    const items = await controlador.getAllLatLngGPSTEST();
    respuesta.success(req, res, items, 200);
  } catch (error) {
    next(error);
  }
}

//Call in HEATMAPCARD
//Call in NETWORKCHART
//Call in MAPSVIEW
async function getAllLatLngPMPAP(req, res, next) {
  try {
    await controlador.getAllLatLngPMPAP(res);
  } catch (error) {
    next(error);
  }
}

async function getAllPolylines(req, res, next) {
  try {
    await controlador.getAllPolylines(res);
  } catch (error) {
    next(error);
  }
}

//Call in HEATMAPCARD
//Call in NETWORKCHART
//Call in MAPSVIEW
//Call in COSTMAPSVIEW
async function getAllLatLngRAJANT(req, res, next) {
  try {
    await controlador.getAllLatLngRAJANT(res);
  } catch (error) {
    next(error);
  }
}

//Call in DASHBOARDVIEW
//Call in HEATMAPSVIEW
async function getCoverage(req, res, next) {
  try {
    await controlador.getCoverage(res);
  } catch (error) {
    next(error);
  }
}

async function getAllHaulTrucks(req, res, next) {
  try {
    await controlador.getAllHaulTrucks(res);
  } catch (error) {
    next(error);
  }
}

async function getAllHaulTrucksDrive(req, res, next) {
  try {
    await controlador.getAllHaulTrucksDrive(res);
  } catch (error) {
    next(error);
  }
}

async function getPositionHaulTrucks(req, res, next) {
  try {
    await controlador.getPositionHaulTrucks(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

async function getPositionDrives(req, res, next) {
  try {
    await controlador.getPositionDrives(res, req.query.ip);
    // await controlador.getPositionDrives(res, '192.168.2.36');
  } catch (error) {
    next(error);
  }
}

async function getPositionDrivesRajant(req, res, next) {
  try {
    await controlador.getPositionDrivesRajant(res, req.query.ip);
    // await controlador.getPositionDrivesRajant(res, '192.168.2.249');
  } catch (error) {
    next(error);
  }
}
// async function getMapCoberturaLatency(req, res, next) {
//   try { await controlador.getMapCoberturaLatency(res);
//   } catch (error) {
//     next(error);
//   }
// }
// async function getMapCoberturaLatLng(req, res, next) {
//   try {
//     await controlador.getMapCoberturaLatLng(res);
//   } catch (error) {
//     next(error);
//   }
// }

module.exports = router;
