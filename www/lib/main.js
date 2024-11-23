// Предопределенные функции. 
// Их можем использовать в tree.xml в атрибуте calc.
// <Tag source="Randomizer" tag="1" calc="psitokpa" name="Какой-то параметр"/>
const CONVERSIONS = { 
  FtoC:function(v){ // Фаренгейты в Цельсии
    return (v-32)*5/9
  },
  psitokpa:function(v){ //psi в кПа
    return v*6.894744825494
  }
}
// main Vue app
let app=null;

const locales = {
  en: {
    appTitle: 'Trend Viewer',
    dateStart: 'From',
    dateEnd: 'To',
    drawButton: 'Draw',
    drawNewButton: 'Draw new',
    dt:{
      h3:'3 hour',
      today: 'Today',
      yestarday: 'Yesterday',
      day3: '3 days',
      day7: '7 days',
      monthCurrent: 'Current month',
      monthPrev: 'Previous month',
      subMonth: '-M',
      subDay: '-D',
      subHour: '-H',
      addHour: '+H',
      addDay: '+D',
      addMonth: '+M',
    },
    btnStatistics: "Statistic",
    btnTable: "Data tables",
    btnExport: "Export",
    btnPrint: "Print",
    btnScreenshot: "Screenshot",
    btnThemeToggle: 'Theme',
    btnLanguage: 'Change language',
    btnSettings: "Settings",
    btnHelp: "Help",
    menuTitle: "Saved sets",
    menuCollapse: "Collapse tree",
    menuUncheck: "Uncheck all",
    menuCheckDrawed: "Check drawed",
    menuSaveList: "Save set",
    menuClearList: "Clear set",
    setPromptName: "Enter set name",
    setPromptDeleteAll:"Are you sure you want to clear the lists?",
    setPromptDeleteOne: "Are you sure you want to delete list ",
    search: 'Search',
    export: {
      title: 'Export to CSV',
      close: 'Close',
      export: 'Export',
      success: 'Export success',
      timeRange: 'Time range',
      timeRangeAll: 'All',
      timeRangeCurrentView: 'Current view',
      decimalSeparator: 'Decimal ceparator',
      interval: 'Interval',
      seconds: 'sec',
      minutes: 'min',
      hour: 'hour',
      day: 'day',
      function: 'Function',
      functionNothing: 'Nothing',
      functionAverage: 'Average',
      functionMin: 'Min',
      functionMax: 'Max',
      functionAll: 'All',
      delimiter: 'Delimiter',
      dateTimeFormatLabel: 'Datetime format',
      dateTimeFormatTitle: 'The specifier string may contain the following directives:'
                    +'\n  %d - zero-padded day of the month as a decimal number [01,31].'
                    +'\n  %H - hour (24-hour clock) as a decimal number [00,23].'
                    +'\n  %I - hour (12-hour clock) as a decimal number [01,12].'
                    +'\n  %j - day of the year as a decimal number [001,366].'
                    +'\n  %m - month as a decimal number [01,12].'
                    +'\n  %M - minute as a decimal number [00,59].'
                    +'\n  %L - milliseconds as a decimal number [000, 999].'
                    +'\n  %p - either AM or PM.*'
                    +'\n  %S - second as a decimal number [00,61].'
                    +'\n  %w - Sunday-based weekday as a decimal number [0,6].'
                    +'\n  %W - Monday-based week of the year as a decimal number [00,53].'
                    +'\n  %x - the locale’s date, such as %-m/%-d/%Y.*'
                    +'\n  %X - the locale’s time, such as %-I:%M:%S %p.*'
                    +'\n  %y - year without century as a decimal number [00,99].'
                    +'\n  %Y - year with century as a decimal number, such as 1999.'
                    +'\n  %Z - time zone offset, such as -0700, -07:00, -07, or Z.',
    },
    analyze: {
      title: 'Statistics',
      name: 'Name',
      tag: 'Tag',
      count: 'Number of points',
      minCom: 'Min common',
      maxCom: 'Max common',
      minCur: 'Min current',
      maxCur: 'Max current',
      desc: 'Description',
      close: 'Close'
    },
    datatables:{
      title: 'Data table',
      select: 'Select',
      headers:{
        date: 'DateTime',
        value: 'Value'
      },
      close: 'Close',
      copy: 'Copy all',
      copy_success: 'Copied!'
    },
    colorPicker: {
      title: 'Color Picker',
      cancel:'Cancel',
      close:'Close'
    },
    settings: {
      title: 'Settings',
      close: 'Close'
    },
    noDataText: 'Nothing'
  },
  ru: {
    appTitle:'Просмотр трендов',
    dateStart: 'Начало',
    dateEnd: 'Конец',
    drawButton: 'Построить',
    drawNewButton: 'Построить на новом',
    dt:{
      h3:'3 часа',
      today: 'Сегодня',
      yestarday: 'Вчера',
      day3: '3 дня',
      day7: '7 дней',
      monthCurrent: 'Текущий месяц',
      monthPrev: 'Прошлый месяц',
      subMonth: '-М',
      subDay: '-Д',
      subHour: '-Ч',
      addHour: '+Ч',
      addDay: '+Д',
      addMonth: '+М'
    },
    btnStatistics: "Статистика",
    btnTable: "Таблицы данных",
    btnExport: "Экспорт",
    btnPrint: "Печать",
    btnScreenshot: "Скриншот",
    btnThemeToggle: 'Тема',
    btnLanguage: 'Change language',
    btnSettings: "Настройки",
    btnHelp: "Справка",
    menuTitle: "Наборы",
    menuCollapse: "Свернуть",
    menuUncheck: "Очистить выделение",
    menuCheckDrawed: "Выбрать нарисованные",
    menuSaveList: "Сохранить набор",
    menuClearList: "Очистить список",
    setPromptName: "Введите имя набора",
    setPromptDeleteAll:"Вы действительно хотите очистить списки?",
    setPromptDeleteOne: "Вы действительно хотите удалить список ",
    search: 'Поиск',
    export: {
      title: 'Экспорт',
      close: 'Закрыть',
      export: 'Сохранить',
      success: 'Успешно',
      timeRange: 'Диапазон',
      timeRangeAll: 'Всё',
      timeRangeCurrentView: 'Текущий вид',
      decimalSeparator: 'Разд. дробной части',
      interval: 'Интервал',
      seconds: 'сек',
      minutes: 'мин',
      hour: 'час',
      day: 'день',
      function: 'Функции',
      functionNothing: 'Нет',
      functionAverage: 'Среднее',
      functionMin: 'Минимум',
      functionMax: 'Максимум',
      functionAll: 'Все',
      delimiter: 'Разделитель',
      dateTimeFormatLabel: 'Формат времени',
      dateTimeFormatTitle: 'Спецификаторы:'
                    +'\n  %d - день [01,31].'
                    +'\n  %H - час [00,23].'
                    +'\n  %I - час [01,12].'
                    +'\n  %j - день в году [001,366].'
                    +'\n  %m - месяц [01,12].'
                    +'\n  %M - минуты [00,59].'
                    +'\n  %L - миллисекунды [000, 999].'
                    +'\n  %p - AM, PM.*'
                    +'\n  %S - секунды [00,61].'
                    +'\n  %w - номер дня в неделе [0,6].'
                    +'\n  %W - номер недели в году [00,53].'
                    +'\n  %y - год без двух цифр [00,99].'
                    +'\n  %Y - год'
                    +'\n  %Z - смещение часового пояса -0700, -07:00, -07, or Z.',
    },
    analyze: {
      title: 'Статистика',
      name: 'Имя',
      tag: 'Тэг',
      count: 'Количество точек',
      minCom: 'Минимум (общ)',
      maxCom: 'Максимум (общ)',
      minCur: 'Минимум (тек)',
      maxCur: 'Максимум (тек)',
      desc: 'Коммент',
      close: 'Закрыть'
    },
    datatables:{
      title: 'Таблицы данных',
      select: 'Выберите данные',
      headers:{
        date: 'Дата Время',
        value: 'Значение'
      },
      close: 'Закрыть',
      copy: 'Копировать всё',
      copy_success: 'Скопировано'
    },
    colorPicker: {
      title: 'Выбор цвета',
      cancel:'Отмена',
      close:'Закрыть'
    },
    settings: {
      title: 'Настройки',
      close: 'Закрыть'
    },
    noDataText: 'Пусто',
    dataFooter: {
      itemsPerPageText: 'Записей на странице:',
      itemsPerPageAll: 'Все',
      nextPage: 'Следующая страница',
      prevPage: 'Предыдущая страница',
      firstPage: 'Первая страница',
      lastPage: 'Последняя страница',
      pageText: '{0}-{1} из {2}',
    },
    dataTable: {
      itemsPerPageText: 'Записей на странице:',
      ariaLabel: {
        sortDescending: 'Упорядочено по убыванию.',
        sortAscending: 'Упорядочено по возрастанию.',
        sortNone: 'Не упорядочено.',
        activateNone: 'Активируйте, чтобы убрать сортировку.',
        activateDescending: 'Активируйте для упорядочивания убыванию.',
        activateAscending: 'Активируйте для упорядочивания по возрастанию.',
      },
      sortBy: 'Сортировать по',
    },
    
  }
}

const charts = [];
const timeformat = {
  full: d3.time.format("%Y/%m/%d %H:%M:%S.%L"),
  time: d3.time.format("%H:%M:%S.%L"),
  timems: d3.time.format("%H:%M:%S.%L"),
  exportfilename:d3.time.format("%Y%m%d_%H%M%S"),
}


const resizeObserver = new ResizeObserver(entries => {
  entries.forEach((e)=>{
    charts.forEach((c)=>{
      if (c.options.element===e.target) 
        c.onresize();
    })
  })
});


async function draw(chart, tree_element){
  let tag = tree_element.tag;
  let source = tree_element.source;
  let start = app.datestart;
  let end = app.dateend;
  // tag = 165;
  // start = "2023-10-01 00:00";
  // end = "2023-10-31 00:00";
  // source = "fast";
  try {
    if (chart.lines && chart.lines.length>40){
      throw new Error(`Too many lines in chart`);
    }
    
    if (!tag)    { throw new Error(`Parameter "tag" failed. ${tree_element.name}`) }
    if (!source) { throw new Error(`Parameter "source" failed. ${tree_element.name}`) }
    if (!start)  { throw new Error(`Parameter "datestart" failed. ${tree_element.name}`) }
    if (!end)    { throw new Error(`Parameter "dateend" failed. ${tree_element.name}`) }
    
    
    let datasource
    
    // данные можно не с локального сервера брать
    for (let i=0;i<app.sources.length;i++){
      if (app.sources[i]['source']==source){
        datasource = app.sources[source]
        break
      }
    }
    if (datasource===undefined){
      // По умолчанию
      datasource = new DataSource({source})
    }

    // Получаем данные
    let data = await datasource.values(tag, start, end);

    // Преобразования если есть
    if (tree_element.calc) {
      if (Object.keys(CONVERSIONS).indexOf(tree_element.calc)!==-1) {
        data.forEach((e)=>{
          e.v = CONVERSIONS[tree_element.calc](e.v)
        })
      } else {
        // example: v*45+43
        data.forEach((e)=>{
          e.v = eval(tree_element.calc.replaceAll('v',(e.v).toString()))
        })
      }
    }

    // Определяем дискрет
    let isDiscrete;
    if (tree_element.type=="b") { // Если указано в дереве
      isDiscrete = true
    } else {
      isDiscrete = data.every((e)=> e.v == 1 || e.v ==0 )
    }
    
    // Загружаем в график
    chart.load({
      data:data, 
      interpolate: "step-after", // step-after , linear
      tag: tag,
      title: tree_element.name,
      tooltip:tree_element.name,
      type: isDiscrete ? "discrete":"lines",
      attributes: {
        unique_key: tree_element['unique_key'],
        source: tree_element['source'],
        calc: tree_element['calc'],        
      }
    });
    return true;
  } catch (err){
    app.addAlert(err)
    throw err
  }
}


async function drawTree(){
  function async_d3_xml(arg) {
    return new Promise((resolve, reject) => {
      d3.xml(arg, (error, result) => {
        if (error) {
          reject(error); 
        } else {
          resolve(result);
        }
      });
    });
  }
  function makeTreeRecursive(node, result, unique_key, source=""){
    let source_new = node.hasAttribute("source")?node.getAttribute("source"):source
    let tmp = {}
    for (let j=0;j<node.attributes.length;j++){
      try {
        tmp[node.attributes[j].name] = node.attributes[j].value
      } catch (err){ console.trace(err); }
    }
    tmp['unique_key'] = "Node_"+unique_key
    tmp['source'] = source_new
    if (node.children.length>0){
      tmp['children'] = []
      tmp['name']=node.hasAttribute("name")?node.getAttribute("name"):tmp['unique_key']
      for (let i=0; i<node.children.length; i++) {
        makeTreeRecursive(node.children[i],tmp['children'], `${unique_key}_${i}`,source_new);
        tmp.children[i]['parent']=tmp
      }
    } else {
      // tmp['unique_key'] = "Node"+unique_key
      tmp['tag'] = node.getAttribute("tag")
      tmp['unique_key'] += ":" +tmp["tag"]
      tmp['name']=node.hasAttribute("name")?node.getAttribute("name"):node.getAttribute("tag")
      if (!tmp['name']) tmp['name']=tmp['unique_key']
      if (!tmp["title"]) tmp["title"] = ""
    }
    result.push(tmp)    
  }
  
  app.treeLoading = true
  
  let result = []
  let root_id = 0
  // 1. Custom tree
  const path = "tree.xml";
  const treexml = await async_d3_xml(path) 
  makeTreeRecursive(treexml.children[0],result, root_id++, "")
  app.tree = result
  
  // 2. Dynamic tree
  let response = await fetch('/api/tree')  // Все элементы с сервера
  if (!response.ok) {
    app.treeLoading = false
    let message = await response.text()
    throw new Error(message)
  }

  let responce_json = await response.json()
  if (responce_json.error) {
    throw new Error(`Request error tag=${tag} error=${json.error}`)
  } 

  const parser = new DOMParser();
  Object.keys(responce_json.data).forEach((source)=>{
    try {
      const xmlString = responce_json.data[source];
      const xmlDoc = parser.parseFromString(xmlString.replaceAll("&amp;","&"), "application/xml");
      let result = [];
      let source_name = source
      try {
        // Меняем имя в дереве если источник описан ранее с коротким именем
        for (let i=0;i<app.sources.length;i++){
          if (app.sources[i].options.source==source){
            source_name = app.sources[i].options.shortname
            break
          }
        }  
      } catch {}
      
      xmlDoc.children[0].setAttribute('name',source_name )
      makeTreeRecursive(xmlDoc.children[0],result, root_id++, source)
      result.forEach((n)=>{
        app.tree.push(n);
      })
    } catch (err){
      app.addAlert(`Tree ${source} failed`)
      console.error(err)
    }
  })
  app.treeLoading = false
}

function findTreeRecursive(tree,filter={}){
  if (tree instanceof Array){
    for (let i=0; i<tree.length; i++) {
      let res = findTreeRecursive(tree[i], filter)
      if (res) return res
    }
  }
  if (Object.keys(filter).every(k=>tree[k]==filter[k])){
    return tree
  }
  if (tree['children']) {
    return findTreeRecursive(tree['children'], filter)
  } 
  return null
}

function getSomeLine(){
  for (let i=0;i<charts.length;i++)
    for(let j=0;j<charts[i].lines.length;j++)
      return charts[i].lines[j]
}


function datetimeparse(dt){
  // used for app bar buttons
  return new Date(dt)
}

function datetimeformat(dt){
  // used for app bar buttons
  // Использум готовую функцию с d3. Если нужно просто перепишите
  return d3.time.format("%Y-%m-%d %H:%M:%S")(dt)
}

function main() {
  app = new Vue({
    el: '#app',
    vuetify: new Vuetify({
      theme: { dark: localStorage.getItem('darkTheme')==='true'?true:false},
      lang: { 
        locales: locales, 
        current: localStorage.getItem('lang')==='ru'?'ru':'en'
      }
    }),
    data: () => ({
      // title: '',
      tree: [],
      tree_selected:[],
      tree_open: [],
      tree_search:null,

      treeLoading: true,
      chartLoading: false,
      sidebarExpanded: true,
      datestart: new Date(), // -1 час
      dateend: new Date(),
      alerts: [],
      set_saved: [],
      sources: [ //Сюда добавляем описания своих источников для дерева
        // new Masterscada({source: 'Masterscada_fast', shortname: 'Краткосрочный архив', description: 'Краткосрочный архив Masterscada 30 дней'}),
        // new Masterscada({source: 'Masterscada_main', shortname: 'Основной архив'}),
        new DataSource({source: 'Randomizer', shortname: 'Super random generator'})
      ]
    }),
    created: function () {
      let tmp;
      Chart.setLocale(this.$vuetify.lang.current)
      try {
        this.datestart = datetimeformat(new Date(new Date().getTime() - 8*3600000));
        this.dateend = datetimeformat(new Date());
      } catch (err) { console.trace(err); }
      
      try {
        tmp = localStorage.getItem('set_saved');
        if (tmp) {
          this.set_saved = JSON.parse(tmp);
        }
      } catch (err) { console.trace(err); }
    },
    watch: {
      tree_selected (val) {
        if (!this.treeLoading) return;
        if ((this.tree_selected.length>0)&&(!menu_links.chart_draw.enabled)){
          menu_links.chart_draw.enabled = true;
          menu_links.chart_drawnew.enabled = true;
          Chart.menu.chart.items[3].enabled = true;
        }
        if ((this.tree_selected.length==0)&&(menu_links.chart_draw.enabled)){
          menu_links.chart_draw.enabled = false;
          menu_links.chart_drawnew.enabled = false;
          Chart.menu.chart.items[3].enabled = false;
        }
      },
      treeLoading (val){
        if (val) return
        sessionStorage
        try {
          this.tree_open = JSON.parse(sessionStorage.getItem("tree_open")).map(unique_key => 
            findTreeRecursive(this.tree, {unique_key: unique_key}));
        } catch (err) { console.trace(err); }
      }
    },
    methods:{
      t(key){ // short translator
        return this.$vuetify.lang.t(key)
      },
      addAlert(err){
        let result = { type: 'error', text: err}
        if (err instanceof Error) {
          result["text"] = `${err.name}: ${err.message}`
          console.error(err)
        } else {
          if (err["type"] && err["text"]){
            result["type"] = err["type"]
            result["text"] = err["text"]
          } 
        }
        app.alerts.push(result)
        setTimeout(()=>{
          app.alerts.shift()
        },3000)
      },
      localeToggle(){
          this.$vuetify.lang.current = this.$vuetify.lang.current=='en'? 'ru':'en';
          let current = this.$vuetify.lang.current
          modal_app.$vuetify.lang.current = current=='en'? 'en':'ru';
          localStorage.setItem('lang',current);
          Chart.setLocale(current)
      },
      restrictInput(event) {
        const allowedChars = /[0-9:-\s]/;
        if (!allowedChars.test(event.key)) {
          event.preventDefault();
        } 
      },
      formatDateTime() {
        const dateTimePattern = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
        if (!dateTimePattern.test(this.dateTime)) {
          this.dateTime = "";
        }
      },
      validateDateTime(value) {
        const dateTimePattern = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
        return dateTimePattern.test(value) || "Введите корректную дату и время (YYYY-MM-DD HH:mm:ss)";
      },
      treeviewClick(item, recursive, expand){
        let index
        if (!item['children'] && expand === undefined) {
          index = this.tree_selected.indexOf(item)
          if (index===-1){
            this.tree_selected.push(item)
            if (this.tree_selected.length>10) {
              this.addAlert({type: "warning", text:"Выбрано больше 10 тегов, будет построены первые 10 выбранных."})
            }
          } else {
            this.tree_selected.splice(index,1)
          }
          return
        }
        if (item['children']) { // Раскрываем группу
          index = this.tree_open.indexOf(item);
          let save = false
          if (expand===undefined) {
            if (index===-1) {
              this.tree_open.push(item)
              expand = true
            } else {
              this.tree_open.splice(index,1)
              expand = false
            }
            save = true
          } else {
            if (expand) {
              if (index===-1) this.tree_open.push(item)
            } else {
              if (index!==-1)this.tree_open.splice(index,1)
            }
          }
          if (recursive===true){
            item['children'].forEach(e=>{
              if (e['children'])
                this.treeviewClick(e, recursive, expand)
            })
          }
          if (save) sessionStorage.setItem("tree_open",JSON.stringify(this.tree_open.map(e=>e.unique_key)))
        }
        // Старый вариант без open
        // e.target.parentElement.parentElement.parentElement.querySelector('button').click();
      },
      async drawselected(addchart=false){
        if (this.tree_selected.length==0) {
          this.addAlert(this.t('$vuetify.noDataText'));
          return;
        }
        this.chartLoading = true
        let chart;
        let chartarea;
        if (charts.length===0 || addchart===true){
          // await requestAnimationFrame(a=>{}) //Ждет рендеринга
          chartarea = d3.select("#chartcontainer")
            .append("div")
            .classed("chartarea", true)
            .style("height",charts.length>0?Math.floor(1000/charts.length)/10+"%":"100%")
            .node();
          addchart = true;
          chart = new Chart.Chart({element: chartarea})
        } else {
          chart = charts[charts.length-1]
        }

        let some_success = false
        // 1) Запросы выполняются параллельно. 
        // let results = await Promise.allSettled(this.tree_selected.map((e) => draw(chart, e)))
        // results.forEach((result) => {
        //   if (result.status=="fulfilled"){
        //     some_success = true
        //   }
        // })
        
        // 2) Здесь запросы выполняются по очереди. Мы никуда не спешим :)
        for (let i=0;i<this.tree_selected.length;i++) {
          try {
            await draw(chart, this.tree_selected[i]);
            some_success = true
          } catch (err) {
            // 
          }
        }
        
        this.tree_selected = [];
        if (addchart) {
          if (some_success){ 
            charts.push(chart);
            d3.selectAll(".chartarea")
              .style("height",Math.floor(1000/charts.length)/10+"%");
            resizeObserver.observe(chartarea);
            chart.onresize()
          } else {
            chart.destroy();
            chartarea.remove();
          }
        }
        this.chartLoading = false
      },
      async drawnum(num){
        if (num>charts.length-1) return;
        if (num<0) return;
        this.chartLoading = true
        const chart = charts[num]

        for (let i=0;i<this.tree_selected.length;i++) {
          try {
            await draw(chart, this.tree_selected[i]);
          } catch (err) {
          }
        }
        this.chartLoading = false
        this.tree_selected = []
      },
      checkDrawed(){
        let drawed = []
        charts.forEach(c=>c.lines.forEach((l)=>{
          drawed.push(l.attributes.unique_key)
        }))
        let tags_to_select = []
        tags_to_select = drawed.map(uk=>findTreeRecursive(this.tree, {unique_key: uk}))
        this.tree_selected = tags_to_select
      },
      savedSetsSave(){
        if (this.tree_selected.length==0) return;
		    let set_name = prompt(this.t('$vuetify.setPromptName'));
        if (!set_name) return;
        this.set_saved.push({
          title:set_name, 
          items:this.tree_selected.map((e)=>{
            return {
              unique_key:e.unique_key,
              name: e.name,
              tag: e.tag,
              source: e.source
            }
          }),
          open: this.tree_open.map(e=>e.unique_key)
        })
        localStorage.setItem("set_saved", JSON.stringify(this.set_saved))
      },
      savedSetsClear(){
        if (confirm(this.t('$vuetify.setPromptDeleteAll'))){
          this.set_saved = []
          localStorage.removeItem("set_saved")
        }
      },
      savedSetApply(index){
        const tree = this.tree;
        
        // Самый примитивный способ, пока не поменяется дерево.
        // let saved_tags = this.set_saved[index].items.map(unique_key => findTreeRecursive(tree, {unique_key: unique_key}))

        // 
        let saved_tags = this.set_saved[index].items.map(e => {
          let node = findTreeRecursive(tree, {unique_key: e.unique_key, source: e.source})
          if (node) return node

          node = findTreeRecursive(tree, {
            source: e.source,
            name: e.name,
            tag: e.tag
          })
          if (node) return node


          let getTreeNodesAsList = function(nodes,result){
            nodes.forEach((node)=>{
              result.push(node)
              if (node.children){
                getTreeNodesAsList(node.children, result)
              }  
            })
          }
          let treeNodesList = []
          getTreeNodesAsList(tree,treeNodesList)
          treeNodesList=treeNodesList.filter((d)=>{ return (d.tag==e.tag && d.source==e.source) })
          if (treeNodesList.length==0) return
          if (treeNodesList.length==1) return treeNodesList[0]

          for (let j=0;j<e.unique_key.length;j++){
            for (let i=0;i<treeNodesList.length;i++){
              if (treeNodesList[i].unique_key.endsWith(e.unique_key.substr(i))) return treeNodesList[i]
            }
          }
        })        

        this.tree_selected = saved_tags
        let saved_tree_open = []
        saved_tags.forEach((tag)=>{
          let node = tag.parent
          while (node) {
            saved_tree_open.push(node)
            node = node.parent
          }
        })
        this.tree_open = saved_tree_open
        // try {
        //   this.tree_open = this.set_saved[index].open.map(unique_key => findTreeRecursive(tree, {unique_key: unique_key}));
        // } catch (err) { console.trace(err); }
      },
      savedSetRemove(index){
        if (confirm(`${this.t('$vuetify.setPromptDeleteOne')} ${this.set_saved[index].title}?`)){
          this.set_saved.splice(index,1)
          localStorage.setItem("set_saved", JSON.stringify(this.set_saved))
        }
      }
    }
  })

  try{
    drawTree()
  } catch(err){
    app.treeLoading = false
    app.addAlert(err)
  }
    
  d3.select(window).on('resize',function(){
    charts.forEach((c)=>{
      c.onresize()
    })
  });
}


function modal(){
  return new Vue({
    el: '#modal',
    vuetify: new Vuetify({
      lang: { 
        locales: locales,
        current: localStorage.getItem('lang')=='ru'?'ru':'en'
      }
    }),
    data: () => ({
      modal_export: false,
      modal_analyze: false,
      modal_settings: false,
      modal_datatables: false, 
      modal_color_picker: false,
     
      analyze_data: [],
      datatables: {
        headers: [
          { text: '$vuetify.datatables.headers.date', value: 'd', sortable: false, },
          { text: '$vuetify.datatables.headers.value', value: 'v',sortable: false, },
        ],
        items: [],
        select_items: [],
        selected: "",
        all_in: false,
      },

      export_disabled: true,
      export_all: "0",
      export_delimiter: "0",
      export_datetimeformat:"%Y-%m-%d %H:%M:%S.%L",
      export_interval: "0",
      export_decimal_separator: "0",
      export_datetimeformat_test:"",
      color_picker: {
        model: "#00FF00",
        saved: "#000000",
        line: undefined
      }
    }),
    computed:{
      charts: ()=>charts,
      localizedHeaders (){
        return this.datatables.headers.map((d)=>{
          let tmp = Object.assign({},d)
          if (tmp.text.startsWith("$vuetify"))
            tmp.text = this.t(tmp.text)
          return tmp
        })
      },
    },
    watch: {
      modal_export (val){
        let export_saved
        if (!val) { 
          export_saved ={
            export_delimiter: this.export_delimiter,
            export_datetimeformat:this.export_datetimeformat,
            export_interval:this.export_interval,
            export_decimal_separator:this.export_decimal_separator
          }
          localStorage.setItem('export_saved', JSON.stringify(export_saved))
          return
        }
        this.export_disabled = getSomeLine()===undefined
        
        try {
          let tmp = localStorage.getItem('export_saved')
          if (tmp) {
            export_saved = JSON.parse(tmp)
            this.export_delimiter = export_saved.export_delimiter;
            this.export_datetimeformat = export_saved.export_datetimeformat;
            this.export_interval = export_saved.export_interval;
            this.export_decimal_separator = export_saved.export_decimal_separator;
          }
        } catch (err) { console.trace(err); }
      },
      modal_analyze (val) { 
        if (!val) return;
        const buf = [];
        charts.forEach((c)=>{
          const d = c.d3.x.domain();
          c.lines.forEach((l)=>{
            const res = {};
            res.title = l.title;
            res.tag = l.tag;
            res.comment = l.tooltip;
            res.time_start = l.domain.x[0];
            res.time_end = l.domain.x[1];
            res.length = l.data.length;
            res.time_start0 = d[0]
            res.time_end0 = d[1];
            res.min = l.data[0];
            res.max = l.data[0];
            let flag = 0;
            l.data.forEach((v)=>{
              if (v.v<res.min.v) res.min = v;
              if (v.v>res.max.v) res.max = v;
              if (flag==0){ // Устанавливаем первоначальные значения
                if (v.d>=res.time_start0) {
                  res.min0 = v;
                  res.max0 = v;
                  flag = 1
                }
              }
              if (flag==1){
                if (v.d<=res.time_end0){
                  if (v.v<res.min0.v) res.min0 = v;
                  if (v.v>res.max0.v) res.max0 = v;
                } else flag=2;
              } 
            });
            buf.push([res.title,
              res.tag,
              res.length.toString(),
              res.min.v.toString()+"<br/>"+timeformat.full(res.min.d),
              res.max.v.toString()+"<br/>"+timeformat.full(res.max.d),
              res.min0.v.toString()+"<br/>"+timeformat.full(res.min0.d),
              res.max0.v.toString()+"<br/>"+timeformat.full(res.max0.d),
              res.comment,
            ])
          })
        });
        this.analyze_data = buf;
      },
      modal_datatables (val){
        if (!val) return
        
        let someline = getSomeLine()
        if (someline===undefined){
          this.datatables.select_items = []
          return
        }
        
        let select_items_tmp = []
        let lines_length = []
        charts.forEach((c,i)=>{
          c.lines.forEach((l,j)=>{
            select_items_tmp.push({
              title: l.title,
              id: `${i}_${j}`
            })
            lines_length.push(l.data.length)
          })
        })
        this.datatables.select_items = select_items_tmp
        
        if (lines_length.length<=1){
          this.datatables.all_in = false;
          return;
        }

        // Проверим что размеры одинаковые
        if (!lines_length.every(e=>e==lines_length[0])) {
          this.datatables.all_in = false;
          return;
        }
        
        // Проверим на первые и последние даты для оптимизации
        let first = someline.data[0].d-0;
        if (!charts.every(c=>c.lines.every(l=> l.data[0].d-first==0))) {
          this.datatables.all_in = false;
          return;
        }
          
        let last = someline.data[someline.data.length-1].d-0
        if (!charts.every(c=>c.lines.every(l=> l.data[l.data.length-1].d-last==0))) {
          this.datatables.all_in = false;
          return;
        }
        
        // И понеслась
        let items = []
        for (let i=0;i<lines_length[0];i++){
          let row = { d:someline.data[i].d }
          if (!charts.every((c,ci)=>c.lines.every((l,li)=>{
                              row[`${ci}_${li}`] = l.data[i].v
                              return l.data[i].d-row.d==0
                            }))) {
            this.datatables.all_in = false;
            return;
          }
          items.push(row)
        }
        this.datatables.items = items

        // Нуштош. Придется таблицу делать
        let headers = [{ text: '$vuetify.datatables.headers.date', value: 'd' }]
        charts.forEach((c,i)=>{
          c.lines.forEach((l,j)=>{
            headers.push({
              text: l.title,
              value: `${i}_${j}`
            })
          })
        })
        this.datatables.headers = headers
        this.datatables.all_in = true;
      },
      'datatables.selected'(val){
        if (this.datatables.all_in) return
        let ids = val.split("_").map(Number)
        this.datatables.items = this.charts[ids[0]].lines[ids[1]].data
      },
      'datatables.all_in'(val){
        if (!val){
          this.datatables.headers = [
            { text: '$vuetify.datatables.headers.date', value: 'd', sortable: false, },
            { text: '$vuetify.datatables.headers.value', value: 'v',sortable: false, }
          ]
          this.datatables.selected="0_0"
        }
      },
      'color_picker.model'(val){
        let line_index = -1
        let c
        for (let i=0;i<charts.length;i++){
          line_index = charts[i].lines.indexOf(this.color_picker.line)
          if (line_index!==-1){
            let r=Number("0x"+val.substr(1,2))/255
            let g=Number("0x"+val.substr(3,2))/255
            let b=Number("0x"+val.substr(5,2))/255
            charts[i].updateColor(line_index,r,g,b)
            break
          }
        }
      }
    },
    methods:{
      t(key){ // short translator
        return this.$vuetify.lang.t(key)
      },
      validateExportDateTimeFormat(value){
        try {
          this.export_datetimeformat_test=d3.time.format(value)(new Date())
          return true
        } catch (err){}
        return false
      },
      formatDateTime(item){
        if (item['d']){
          return timeformat.full(item.d)
        } else {
          return timeformat.full(item[0])
        }
      },
      datatables_copy(){
        let buf = this.localizedHeaders.map(d=>d.text).join("\t")
        this.datatables.items.forEach((d)=>{
          buf += "\n"+timeformat.full(d.d)
          Object.keys(d).forEach((k)=>{
            if (k!='d') buf+="\t"+d[k]
          })
        })
        navigator.clipboard.writeText(buf);
        app.addAlert({type:'info', text:this.t('$vuetify.datatables.copy_success')})
      },
      exportCSV(){
        let dt_to_str = d3.time.format(this.export_datetimeformat)
        const delimiter=["\t",';',',','}'][parseInt(this.export_delimiter)]
        const interval=[1000, 60000, 5*60000,10*60000,30*60000,60*60000,24*60*60000][parseInt(this.export_interval)]
        const exportAll = [true, false][parseInt(this.export_all)]
        const decSep = ['.',','][parseInt(this.export_decimal_separator)]

        let buf="time"+delimiter

        let someline = getSomeLine()
        if (someline===undefined) {
          throw Error("No lines")
        }

        let time_start = someline.domain.x[0].getTime()
        let time_end = someline.domain.x[1].getTime()

        if (exportAll){
          charts.forEach(c=>c.lines.forEach((l)=>{
            if (l.domain.x[0].getTime()< time_start) time_start = l.domain.x[0].getTime()
            if (l.domain.x[1].getTime()> time_end) time_end = l.domain.x[1].getTime()
          }))
        } else {
          let domain = charts[0].d3.x.domain()
          time_start = Math.max(time_start, domain[0].getTime());
          time_end = Math.min(time_end, domain[1].getTime()); 
        }

        if (interval === 24*60*60000) {
          let timezone_offset = new Date().getTimezoneOffset()*60*1000
          time_start = Math.ceil((time_start-timezone_offset)/interval)*interval+timezone_offset;
          time_end = Math.floor((time_end-timezone_offset)/interval)*interval+timezone_offset;
        } else {
          time_start = Math.ceil((time_start)/interval)*interval;
          time_end = Math.floor((time_end)/interval)*interval;
        }
        
        let t = time_start;
        let indexes = charts.map((c)=>{ //Вспомогательный массив для хранения текущих индексов
          return c.lines.map((l)=>{
            buf+=l.title+"\t";
            return 0;
          })
        })
        while (t<=time_end){
          buf +="\n"+dt_to_str(new Date(t))+delimiter
          for (let i = 0; i<indexes.length; i++) {
            for (let j = 0; j<indexes[i].length; j++) {
              let max = charts[i].lines[j].data.length-1;
              let data = charts[i].lines[j].data
              while ((indexes[i][j]<max)&&(data[indexes[i][j]+1].d.getTime()<t)) {
                indexes[i][j]++;
              }
              let value = data[indexes[i][j]].v.toString()
              if (decSep!='.') value=value.replaceAll('.',decSep)
              if ((data[0].d.getTime()>t && indexes[i][j]==0) 
                 || data[data.length-1].d.getTime()<t && indexes[i][j]>=data.length-1) value='0'
              buf+=value+delimiter
            }
          }  
          t+=interval;
        };

        // console.log(buf)
        let filename = timeformat.exportfilename(new Date(time_start))+".csv"
        save_text(filename, buf)
        app.addAlert({type:'info', text:this.t('$vuetify.export.success')}) 
      }
    }
  });
}

function save_text(filename, buf){
  const link = document.createElement('a');
  link.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(buf);
  link.download = filename
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

async function save_screenshot() {
  try {
    html2canvas(chartcontainer).then(canvas => {
      const link = document.createElement('a');
      link.href = canvas.toDataURL();;
      link.download = timeformat.exportfilename(new Date())+".png"
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  } catch (err) {
    app.addAlert(err);
  }
}