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


// [["Thermal records", "Week: 30", "Week: 29", "Week: 28", "Week: 27", "Week: 26", "Week: 25"], ["org.clearlinux/mce/thermal", 155444, 28, 2734, 522, 54, 20]]

    function parseData(data) {

        var dataSets = {};

        if (data.length > 0) {
            var weeks = data[0];
            var values = data[1];
            var dataSet = [];
            var labels = values.shift(1);
            weeks.shift(1);

            for(var x in values){
                dataSet.push({
                    label: weeks[x],
                    backgroundColor: rootObj.backgroundColors[x],
                    data: [values[x]]
                });
            }

            dataSets = {
                labels: [labels],
                datasets: dataSet
            };
        }

        return dataSets;
    }

    function renderThermal(ctx, values){

        var parsedData = parseData(values);

        var options = {
            legend: {
                display: true,
                position: "right"
            },
            title: {
                display: false,
            },
            scales: {
                xAxes: [{
                    barThickness: 30
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        };

        rootObj.newChart(ctx, "bar", parsedData, options);
    }

    rootObj.renderThermal = renderThermal;

});
