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
  }, 2000);}

  else {
    console.log("not logged in")
  }


});

//BUY and SELL when clicking the buttons
$(document).ready(function(){
  $("#buttonbuy").click(function(){

    console.log("clicked 1")

    //check if price has a decimal precision of 0.1 and if the quantity is a whole number and if both are > 0
    if (pricefield.value > 0 && quantityfield.value > 0 && quantityfield.value % 1 == 0 && pricefield.value * 100 % 10 == 0){
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
  });
});