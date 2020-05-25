console.log("script.js loaded")

window.onload = function(){
  var user_navbar_eth_balance = document.getElementById("user_navbar_eth_balance");
  var user_navbar_usd_balance = document.getElementById("user_navbar_eth_balance");
}


function get_userdata(){
  $.get("/api/userinfo",function(data,status){
    user_navbar_eth_balance.innerHTML = data.eth_balance;
    user_navbar_usd_balance.innerHTML = data.usd_balance +" and time is " + data.time;
    console.log(data)
  });
};

$(document).ready(function(){
  $("#alert_error").fadeToggle(3000);
});


$(document).ready(function(){
  setInterval(function(){get_userdata()}, 500);
});