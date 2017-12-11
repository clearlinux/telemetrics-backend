/*
 * Copyright 2017 Intel Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

(function(root, factory){

    factory(root);

})(this.telemetryUI, function(rootObj){


    function parseMCEChartData(name, data){

        var dataSet = [];
        var counter = 0
        for(var label in data){
            dataSet.push({
              label: "Week "+label,
              backgroundColor: rootObj.backgroundColors[counter%14],
              data: [data[label]]
            });
            counter++;
        }

        return {
                labels: [name],
                datasets: dataSet
        }
    }


    function renderOneChart(ctx, data, max){

        var options = {
            legend: {
                display: true,
                position: "right"
            },
            title: {
                display: false
            },
            scales: {
                xAxes: [{
                    stacked: false,
                    barThickness: 30
                }]
            }
        };

        rootObj.newChart(ctx, "bar", data, options);



    function renderMCEClass(ctx, labels, values){

        var data = {
            labels: labels,
            datasets: [{
                label: "MCE reports by classification",
                backgroundColor: rootObj.backgroundColors,
                data: values
            }]
        };

        var options = {
            title: {
                display: true,
                text: "MCE reports by classification",
                fontSize: 18
            },
            legend: {
                position: 'right'
            }
        };


        rootObj.newChart(ctx, "pie", data, options);
    }


    function renderMCEReports(ctx, labels, values){

        var data = {
            labels: labels,
            datasets:[
                {
                    label: "MCE reports by build",
                    data: values
                }
            ]
        };

        var options = {
            legend: { display: false },
            title: {
                display: true,
                text: "MCE reports by build",
                fontSize: 18
            },
            scales: {
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: "MCE count",
                        fontSize: 15,
                        fontStyle: "italic"
                    },
                    ticks: {
                        beginAtZero: true
                    }
                }],
                xAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: "Builds",
                        fontSize: 15,
                        fontStyle: "italic"
                    },
                    barThickness: 15
                }]
            }
        };

        rootObj.newChart(ctx, "bar", data, options);
    }

    rootObj.renderMCEClass = renderMCEClass;
    rootObj.renderMCEReports = renderMCEReports;
    rootObj.parseMCEChartData = parseMCEChartData;
    rootObj.renderOneChart = renderOneChart;
});
