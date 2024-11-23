(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
  typeof define === 'function' && define.amd ? define(factory) :
  (global = global || self, global.Masterscada = factory());
}(this, function () { 'use strict';
	function datetimeparse(str){
	  /*
	  ** Функция перевода строки в дату. Формат строки YYYY-MM-DD HH:mm:ss
	  */
	  return new Date(
	    str.substr(0,4),
	    str.substr(5,2)-1,
	    str.substr(8,2),
	    str.substr(11,2),
	    str.substr(14,2),
	    str.substr(17,2));
	};

	function Masterscada(options, callback){
		if (!(this instanceof Masterscada)) {
			console.warn('Masterscada is a constructor and should be called with the `new` keyword');
		}
		const defaultOptions = {
          description: "Источник даннных из базы данных sqlite3 MASTERSCADA.",
          source: 'main'
        };
		this.options = { ...defaultOptions, ...options };
		this._init(callback)
	}

	Masterscada.prototype._init = function(callback){
		
	}

	Masterscada.prototype.values = async function (tag, datestart, dateend) {
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
			throw new Error(`Request error tag=${tag}`)
		}
	}
	return Masterscada;
	
}))