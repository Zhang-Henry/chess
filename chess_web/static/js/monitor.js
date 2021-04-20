var taskSizeChart = echarts.init(document.getElementById('taskSize'));
var startTime = new Date();
startTime.setFullYear(2021,2,1)

$(function () {
    $('input').bind('input propertychange', function () {
        $('.commonTable tbody tr').hide()
            .filter(":contains('" + ($(this).val()) + "')").show();
    });

    $("#refreshBtn").click(function () {
        window.location.reload();
    });
    // initTable();
    setInterval(initTable, 1000 * 10);
    setInterval(tick, 1000);
});

function tick(){
    var today = new Date();
    document.getElementById("localtime").innerHTML = showLocale(today);
    // console.log(today)
    var t = today - startTime;
    var day = Math.floor(t/1000/60/60/24);
    $("#runTimeTj").html(day+" 天 ");
}


function taskSizeTj(){
    var option = {
        color: ['#E67E22','#00b3ac'],
        legend: {
            data: ['ELO', 'ELO增减值'],
            x: 'center',
            y: 30,
            textStyle: {
                color: 'white'
            }
        },
        tooltip : {
            trigger: 'axis',
            axisPointer : {
                type : 'shadow'
            }
        },
        xAxis : [
            {
                data : game_numbers,
                type: 'category',
                splitLine:{
                    show: false
                },
                axisLabel: {
                    interval: 0,
                    show: true,
                    textStyle: {
                        color: '#c3dbff',  //更改坐标轴文字颜色
                        fontSize : 14      //更改坐标轴文字大小
                    }
                }
            }
        ],
        yAxis : [
            {
                type : 'value',
                axisLabel: {
                    show: true,
                    textStyle: {
                        color: '#c3dbff'
                    }
                }
            }
        ],
        series : [
            {
                name:'ELO',
                type:'line',
                smooth: true,
                barWidth: '100%',
                data:elu_points
            },
            {
                name:'ELO增减值',
                type:'line',
                smooth: true,
                barWidth: '100%',
                data:delta_elo
            }
        ]
    };
    taskSizeChart.setOption(option);
}

function initTable() {
    taskSizeTj();
    $('.commonTable tbody tr').hide()
        .filter(":contains('" + ($("#searchText").val()) + "')").show();

}

function showLocale(objD){
    var str,colorhead,colorfoot;
    var yy = objD.getYear();
    if(yy<1900) yy = yy+1900;
    var MM = objD.getMonth()+1;
    if(MM<10) MM = '0' + MM;
    var dd = objD.getDate();
    if(dd<10) dd = '0' + dd;
    var hh = objD.getHours();
    if(hh<10) hh = '0' + hh;
    var mm = objD.getMinutes();
    if(mm<10) mm = '0' + mm;
    var ss = objD.getSeconds();
    if(ss<10) ss = '0' + ss;
    var ww = objD.getDay();
    if  ( ww==0 )  colorhead="<font color=\"#ffffff\">";
    if  ( ww > 0 && ww < 6 )  colorhead="<font color=\"#ffffff\">";
    if  ( ww==6 )  colorhead="<font color=\"#ffffff\">";
    if  (ww==0)  ww="星期日";
    if  (ww==1)  ww="星期一";
    if  (ww==2)  ww="星期二";
    if  (ww==3)  ww="星期三";
    if  (ww==4)  ww="星期四";
    if  (ww==5)  ww="星期五";
    if  (ww==6)  ww="星期六";
    colorfoot="</font>"
    str = colorhead + yy + "-" + MM + "-" + dd + " " + hh + ":" + mm + ":" + ss + "  " + ww + colorfoot;
    return(str);
}

function hideBugBtn() {
    $("#bugBtn").hide();
}

