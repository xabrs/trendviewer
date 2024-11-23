/**
Источник данных по умолчанию
*/

(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
  typeof define === 'function' && define.amd ? define(factory) :
  (global = global || self, global.DataSource = factory());
}(this, function () { 'use strict';
	function datetimeparse(str){
	  /*
	  ** Функция перевода строки в дату. Формат строки YYYY-MM-DD HH:mm:ss.fff
	  */
	  return new Date(str)
	  // return new Date(
	  //   str.substr(0,4),
	  //   str.substr(5,2)-1,
	  //   str.substr(8,2),
	  //   str.substr(11,2),
	  //   str.substr(14,2),
	  //   str.substr(17,2));
	};

	function DataSource(options, callback){
		if (!(this instanceof DataSource)) {
			console.warn('DataSource is a constructor and should be called with the `new` keyword');
		}
		const defaultOptions = {
      description: "Источник даннных",
      source: 'source'
    };
		this.options = { ...defaultOptions, ...options };
		this._init(callback)
	}

	DataSource.prototype._init = function(callback){
		
	}

	DataSource.prototype.values = async function (tag, datestart, dateend) {
		let result =[];
		const response = await fetch(`api/values?source=${this.options.source}&tag=${tag}&start=${datestart}&end=${dateend}`);
	  if (response.ok) {
	    const res = await response.json()
	    if (res.error) {
	    	throw new Error(`Request error tag=${tag} error=${json.error}`)
	    } else {
	      result = res.data.map((e)=>{
	        return {
	          v: e.v,
	          d: datetimeparse(e.dt)
	        }
	      })
	      if (result.length<2){
	      	throw new Error(`Нет данных по запросу tag=${tag}, ${datestart} - ${dateend}`)
	      }
			}	
			return result
		} else {
			let text = `Request error tag=${tag}`
			try{
				text+=`\n${await response.text()}`
			} finally {}
			throw new Error(text)
		}
	}
	return DataSource;
	
}))