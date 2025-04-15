const db = require("../../DB/mysql");

function getClustering(res) {
  return db.getClustering(res);
}

function getClusteringData(res, fecha) {
  return db.getClusteringData(res, fecha);
}

function getLast12HourClustering(res) {
  return db.getLast12HourClustering(res);
}

module.exports = {
  getClustering,
  getClusteringData,
  getLast12HourClustering,
};
