const chart = document.querySelector("#chart").getContext('2d');
// create a new chart instance
var data = JSON.parse(document.getElementById('data').dataset.data);
console.log(data);

new Chart(chart , {

    type:'line',
    data : {
        labels :data["dates"],

        datasets:[{
            label : 'Quantity',
            data : data["quantity"],
            borderColor : 'red',
            borderWidth : 2
        },
     
        {
            label : 'SHOP',
            data : [220,323,2,1927,2434451 ,1244451,98297,1262524,122735,992212,1223],
            borderColor : 'blue',
            borderWidth : 2

        },
    ]
    }

})



let menuBtn = document.querySelector("#menu-btn");
let closeBtn = document.querySelector("#close-btn");
let sideBar = document.querySelector("aside");


menuBtn.addEventListener('click' , ()=>{

  sideBar.style.display = 'block';

})

closeBtn.addEventListener('click' , ()=>{

  sideBar.style.display='none';


})

const themeBtn = document.querySelector('.theme-btn');

themeBtn.addEventListener('click', ()=>{

    document.body.classList.toggle('dark-theme');
    themeBtn.querySelector('span:first-child').classList.toggle('active');

    themeBtn.querySelector('span:last-child').classList.toggle('active')

})

