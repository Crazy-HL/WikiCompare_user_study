import axios from "axios";

var address = "http://localhost:8888/";

function filterNull(o) {
    for (var key in o) {
        if (o[key] === null) {
            delete o[key]
        }
        if (toType(o[key]) === 'string') {
            o[key] = o[key].trim()
        } else if (toType(o[key]) === 'object') {
            o[key] = filterNull(o[key])
        } else if (toType(o[key]) === 'array') {
            o[key] = filterNull(o[key])
        }
    }
    return o
}

function apiAxios(type, url, params, callback) {
    if (type === 'GET') {
        axios.get(address + url, { 'params': params })
            .then(response => {
                callback(response.data); // 获取数据
            })
            .catch(error => {
                console.error('There was an error for GET request!', error);
            });
    }

    if (type === 'POST') {
        axios.post(address + url, params, { headers: { 'Content-Type': 'application/json' } })
            .then(response => {
                callback(response.data); // 获取数据
            })
            .catch(error => {
                console.error('There was an error for POST request!', error);
            });
    }
}

export function postJson(url, params) {
    return axios
        .post(address + url, params, { headers: { "Content-Type": "application/json" } })
        .then(response => response.data);
}

export default {
    get: function (url, params, callback) {
        return apiAxios('GET', url, params, callback);
    },
    post: function (url, params, callback) {
        return apiAxios('POST', url, params, callback);
    }
};
