console.log("script.js loaded")

window.onload = function(){
  var user_navbar_eth_balance = document.getElementById("user_navbar_eth_balance");
  var user_navbar_usd_balance = document.getElementById("user_navbar_eth_balance");
  var quantityfield = document.getElementById("quantityfield");
  var pricefield = document.getElementById("pricefield");
}


function get_userdata(){
$.get("/api/userinfo",function(data,status){
      user_navbar_eth_balance.innerHTML = data.eth_balance;
      user_navbar_usd_balance.innerHTML = data.usd_balance +" and time is " + data.time;
      console.log("get_userdata : " + status)
      return status.status;
    });
};

function get_openorders(){
$.get("/api/openorders",function(data,status){
    openorders = data[0]
    console.log(openorders)
    console.log(openorders.length)

    var openorder_table = document.getElementById("openorder_table");
    console.log("num of rows " + openorder_table.rows.length)
    
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
      $(cancel_row).html('<div style="position: fixed ; "><button type="button" id="'+ element.order_id + '" class="close text-danger rounded-circle border-white" aria-label="Close" onclick="orderdeleteclick(this.id)"><span aria-hidden="true">&times;</span></button></div>');
    }
    });
  };


$(document).ready(function(){
  $("#alert_error").fadeToggle(3000);
});

$(document).ready(function(){
  //makes sure get_userdata is only being requested when user is logged in (the balances in the nav is being shown)
  if($("#user_navbar_eth_balance").is(":visible")){
  setInterval(function(){
    get_userdata()
  }, 2000);}
  else {
    console.log("not logged in")
  }
});

$(document).ready(function(){
  $("#getopenorders").click(function(){
    get_openorders()
  });
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
      },function(data, status){
          console.log("Data: " + data + "\nStatus: " + status);
          console.log(pricefield.value + " " + pricefield.value * 100 % 10 + " quantity " + quantityfield.value + " " +quantityfield.value % 1)
        });
        setTimeout(get_openorders,100)
    }
    else{
      console.log(pricefield.value + " "+ pricefield.value * 100 % 10 + " quantity " + quantityfield.value + " " +quantityfield.value % 1)
      alert("Invalid fields")
    }

});

  $("#buttonsell").click(function(){
    console.log("clicked 1")
    $.post("/api/sendorder",
    {
      pair: "ETHUSD",
      price: pricefield.value,
      quantity: quantityfield.value,
      type: "S",
      ordertype: "L"
    },
    function(data, status){
      console.log("Data: " + data + "\nStatus: " + status);
    });
    setTimeout(get_openorders,100)
  });
});

function orderdeleteclick(order_id){
  $.ajax({
    url: 'api/sendorder',
    type: 'DELETE',
    data: {
      order_id: order_id
    }
    });
    setTimeout(get_openorders,100)
  };
