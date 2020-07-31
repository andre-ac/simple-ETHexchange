console.log("script.js loaded")


window.onload = function(){
  var user_navbar_eth_balance = document.getElementById("user_navbar_eth_balance");
  var user_navbar_usd_balance = document.getElementById("user_navbar_eth_balance");
  var quantityfield = document.getElementById("quantityfield");
  var pricefield = document.getElementById("pricefield");
}


function get_userdata(){
$.get("/api/userinfo",function(data,status){
      user_navbar_eth_balance.innerHTML = data.eth_balance + " (Available:"+ data.available_eth_balance + ")";
      user_navbar_usd_balance.innerHTML = data.usd_balance + " (Available:"+ data.available_usd_balance + ")";
      console.log("get_userdata : " + status)
      return status.status;
    });
};

function get_orderbook(){
$.get("/api/orderbook",function(data,status){
  var data_array = Array.from(data)
  data.sort(function(a, b){return a.price - b.price});
  data_array.sort(function(a, b){return b.price - a.price});

  var bid = []
  var ask = []


  for (var i in data_array) {
    const element_rev = data_array[i]
    const element_sort = data[i]
    
    if (element_rev.type == String("B")){
      bid.push(element_rev.price,element_rev.quantity)
    }
    // ERROR HERE , TYPE IS S BUT ITS NOT RECOGNIZING IT AS S
    if (element_sort.type == "S"){
      ask.push(element_sort.price,element_sort.quantity)
    }
  };

//this fills any reminaing spot of ask and bids until the 8th place to assure that the orderbook doesnt show as undefined
for (let index = 0; index < 8; index++) {
  
  if (typeof bid[index] == "undefined"){
    bid[index] = "---"
  }

  if (typeof ask[index] == "undefined"){
    ask[index] = "---"
  }

  
}

  document.getElementById("bid1-price").innerHTML = bid[0]
  document.getElementById("bid1-size").innerHTML = bid[1]
  document.getElementById("bid2-price").innerHTML = bid[2]
  document.getElementById("bid2-size").innerHTML = bid[3]
  document.getElementById("bid3-price").innerHTML = bid[4]
  document.getElementById("bid3-size").innerHTML = bid[5]
  document.getElementById("bid4-price").innerHTML = bid[6]
  document.getElementById("bid4-size").innerHTML = bid[7]

  document.getElementById("ask1-price").innerHTML = ask[0]
  document.getElementById("ask1-size").innerHTML = ask[1]
  document.getElementById("ask2-price").innerHTML = ask[2]
  document.getElementById("ask2-size").innerHTML = ask[3]
  document.getElementById("ask3-price").innerHTML = ask[4]
  document.getElementById("ask3-size").innerHTML = ask[5]
  document.getElementById("ask4-price").innerHTML = ask[6]
  document.getElementById("ask4-size").innerHTML = ask[7]
});
};

function uniqByKeepLast(a, key) {
  return [
      ...new Map(
          a.map(x => [key(x), x])
      ).values()
  ]
}

function chart(returnData){
  
  console.log("Data is " + returnData)

  var charid = document.getElementById("chartContainer")
    
  var chart = LightweightCharts.createChart(charid, 
      { width: 700, height: 300 } 
      );

      chart.applyOptions({
        layout: {
            backgroundColor: '#fffef2',
            textColor: '#000000',
            fontSize: 12,
            fontFamily: 'Calibri'}
      });
      
      var lineSeries =
       chart.addLineSeries({
        title: 'ETHUSD',
        color:'#000000'});
        
  setInterval(function(){
  fetch("/api/tradehistory")
  .then(function(response) {
    return response.json();
  })
  .then(function(data,response) {    
    console.log("Data loaded ")
    cleaned_data = uniqByKeepLast(data, a => a.time)
    lineSeries.setData(cleaned_data.map(line => {
      //make sure there aren't repeated times
    	return { time: line.time , value: line.price };
    }));
  })},1000)


  chart.timeScale().fitContent();

  lineSeries.applyOptions({
      priceFormat: {
          type: 'custom',
         minMove: 0.01,
          formatter: price => '$' + price.toFixed(2),
      }
  })
};

function get_openorders(){
$.get("/api/openorders",function(data,status){
    openorders = data[0]
    console.log(openorders)
    console.log(openorders.length)

    var openorder_table = document.getElementById("openorder_table");
    console.log("nuem of rows " + openorder_table.rows.length)
    
    while (openorder_table.rows.length>1) {
      openorder_table.deleteRow(1);
    }
    
    let timenow = Math.round( Date.now() / 1000)

    for (let index = 0; index < openorders.length; index++) {
      
      const element = openorders[index];
      const row = openorder_table.insertRow(1)
      if (element.type == "B") {
        row.style.backgroundColor = "#ebffeb";
        row.insertCell(0).innerHTML = "Buy";
      }else {
        row.style.backgroundColor = "#ffd6d6";
        row.insertCell(0).innerHTML = "Sell";
      }
      if (element.ordertype) {
        row.insertCell(1).innerHTML = "Limit";
      }

      row.insertCell(2).innerHTML = element.price
      row.insertCell(3).innerHTML = element.quantity
      row.insertCell(4).innerHTML = element.filled
      
      if ((timenow-element.time) < 3600) {
        row.insertCell(5).innerHTML = moment.unix(element.time).fromNow();
      } else {
        row.insertCell(5).innerHTML = moment.unix(element.time).format('DD, MMM - kk:mm:ss');
      }
          
      const cancel_row = row.insertCell(6)
      $(cancel_row).html('<div><button type="button" id="'+ element.order_id + '" class="close text-danger rounded-circle border-white" aria-label="Close" onclick="orderdeleteclick(this.id)"><span aria-hidden="true">&times;</span></button></div>');
    }
    });
  };


$(document).ready(function(){
  $("#alert_error").fadeToggle(3000);
});

$(document).ready(function(){
  //makes sure get_userdata is only being requested when user is logged in (the balances in the nav is being shown)
  if($("#user_navbar_eth_balance").is(":visible")){
  get_userdata()
  setInterval(function(){
    get_userdata()
  }, 10000);}
  else {
    console.log("not logged in")
  }
});

$(document).ready(function(){
  $("#getopenorders").click(function(){
    get_openorders()
    get_orderbook()
  });
    if($("#buttonbuy").is(":visible")){
      get_openorders()
      get_orderbook()
      setInterval(function(){
        get_orderbook()
      }, 2000);}
    
});

//BUY and SELL when clicking the buttons
$(document).ready(function(){
  $("#buttonbuy").click(function(){
    //check if price has a decimal precision of 0.1 and if the quantity is a whole number and if both are > 0
    if (pricefield.value > 0 && quantityfield.value > 0 && quantityfield.value * 1000 % 10 == 0 && pricefield.value * 100 % 10 == 0){
      $.post("/api/sendorder",
      {
        pair: "ETHUSD",
        price: pricefield.value,
        quantity: quantityfield.value,
        type: "B",
        ordertype: "L"
      })
      .done( function(msg){
        setTimeout(get_openorders,300)
        setTimeout(get_orderbook,300)} )
      .fail( function(xhr, textStatus, errorThrown) {
        alert(xhr.status +": " + xhr.responseJSON.result)
      });
    }
    else{
      console.log(pricefield.value + " "+ pricefield.value * 100 % 10 + " quantity " + quantityfield.value + " " +quantityfield.value % 1)
      alert("Invalid fields")
    }

});

  $("#buttonsell").click(function(){

    if (pricefield.value > 0 && quantityfield.value > 0 && quantityfield.value * 1000 % 10 == 0 && pricefield.value * 100 % 10 == 0){
    $.post("/api/sendorder",
    {
      pair: "ETHUSD",
      price: pricefield.value,
      quantity: quantityfield.value,
      type: "S",
      ordertype: "L"
    })
    .done( function(msg){
      setTimeout(get_openorders,300)
      setTimeout(get_orderbook,300)} )
    .fail( function(xhr, textStatus, errorThrown) {
      alert(xhr.status +": " + xhr.responseJSON.result)
    });
    }
    else{
      console.log(pricefield.value + " "+ pricefield.value * 100 % 10 + " quantity " + quantityfield.value + " " +quantityfield.value % 1)
      alert("Invalid fields")
    }
  });

});

function orderdeleteclick(order_id){
  $.ajax({
    url: 'api/sendorder',
    type: 'DELETE',
    data: {
      order_id: order_id
    }
    })
    .done( function(msg){
      setTimeout(get_openorders,300)
      setTimeout(get_orderbook,300)} )
    .fail( function(xhr, textStatus, errorThrown) {
      alert(xhr.status +": " + xhr.statusText)
    });
  };
