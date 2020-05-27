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


$(document).ready(function(){
  $("#alert_error").fadeToggle(3000);
});

$(document).ready(function(){

  //makes sure get_userdata is only being requested when user is logged in (the balances in the nav is being shown)
  if($("#user_navbar_eth_balance").is(":visible")){
  setInterval(function(){
    get_userdata()
  }, 10000);}

  else {
    console.log("not logged in")
  }


});

//BUY
$(document).ready(function(){
  $("#buttonbuy").click(function(){
    console.log("clicked 1")
    $.post("/api/sendorder",
    {
      pair: "ETHUSD",
      price: pricefield.value,
      quantity: quantityfield.value
    },
    function(data, status){
      console.log("Data: " + data + "\nStatus: " + status);
    });
  });
});