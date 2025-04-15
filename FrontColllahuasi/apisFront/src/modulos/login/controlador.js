const db = require('../../DB/mysql');

function getUserLogin(user,pass){
    return db.getUserLogin(user,pass);
}

module.exports = {
    getUserLogin,
}