const express = require("express");

const respuesta = require("../../red/respuestas");
const controlador = require("./controlador");

const router = express.Router();

router.get("/getAllTopologyData", getAllTopologyData);
router.get("/getGraphTopologyData", getGraphTopologyData);
router.get("/getTableTopologyData", getTableTopologyData);
router.get("/getStatusLogGraph", getStatusLogGraph);
router.get("/getStatusByIP", getStatusByIP);
router.get("/getLatencyByEquip/:ip", getLatencyByEquip);
router.get("/getLastGPSInfoRAJANT", getLastGPSInfoRAJANT);
router.get("/getLastGPSInfoPMP", getLastGPSInfoPMP);
router.get("/getSNMPDataByIP", getSNMPDataByIP);
router.get("/getSNMPUpDateDataByIP", getSNMPUpDateDataByIP);
router.get("/getAllOperabilityByIP", getAllOperabilityByIP);
router.get("/getAllOperabilityLastDay", getAllOperabilityLastDay);
// router.get("/statuslogbyip", getStatusHistoryByIP);
// router.post("/network", allNetworkData);
// router.post("/statuslog", statusLogGraph);

//Call in LISTTOPOLOGY
//Call in DASHBOARDVIEW
//Call in PREDICTVIEW
//Call in SNRMAPSVIEW
//Call in STATUSALARMALERT
async function getAllTopologyData(req, res, next) {
  try {
    await controlador.getAllTopologyData(res);
  } catch (error) {
    next(error);
  }
}

// Call in ANOTHERGRAPHS
// Call in PMP-AP
// Call in PMP-SM
async function getGraphTopologyData(req, res, next) {
  try {
    await controlador.getGraphTopologyData(req.query.ip, req.query.type, res);
  } catch (error) {
    next(error);
  }
}

// Call in PMP-AP
async function getTableTopologyData(req, res, next) {
  try {
    await controlador.getTableTopologyData(req.query.ip, res);
  } catch (error) {
    next(error);
  }
}

// async function allNetworkData(req, res, next) {
//   try {
//     const items = await controlador.getNetworkData();
//     respuesta.success(req, res, items, 200);
//   } catch (error) {
//     next(error);
//   }
// }

//Call in MAPSVIEW
//Call in STATUS-LOG
async function getStatusLogGraph(req, res, next) {
  try {
    await controlador.getstatusLogGraph(req.query.ip, res);
  } catch (error) {
    next(error);
  }
}

async function getStatusByIP(req, res, next) {
  try {
    await controlador.getStatusByIP(req.query.ip, res);
  } catch (error) {
    next(error);
  }
}

async function getAllOperabilityByIP(req, res, next) {
  try {
    await controlador.getAllOperabilityByIP(req.query.ip, res);
  } catch (error) {
    next(error);
  }
}

// async function getStatusHistoryByIP(req, res, next) {
//   try {
//     await controlador.getStatusHistoryByIP(req.query.ip, res);
//   } catch (error) {
//     next(error);
//   }
// }

//Call in COSTMAPSVIEW
//Call in MAPSVIEW
async function getLatencyByEquip(req, res, next) {
  try {
    await controlador.getLatencyByEquip(req.params.ip, res);
  } catch (error) {
    next(error);
  }
}

//Call in STATUS-LOG
async function getLastGPSInfoPMP(req, res, next) {
  try {
    await controlador.getLastGPSInfoPMP(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

//Call in STATUS-LOG
async function getLastGPSInfoRAJANT(req, res, next) {
  try {
    await controlador.getLastGPSInfoRAJANT(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

async function getSNMPDataByIP(req, res, next) {
  try {
    await controlador.getSNMPDataByIP(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}

async function getSNMPUpDateDataByIP(req, res, next) {
  try {
    await controlador.getSNMPUpDateDataByIP(res, req.query.ip);
  } catch (error) {
    next(error);
  }
}


async function getAllOperabilityLastDay(req, res, next) {
  try {
    await controlador.getAllOperabilityLastDay(res);
  } catch (error) {
    next(error);
  }
}

module.exports = router;
