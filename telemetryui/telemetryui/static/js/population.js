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


    function renderChart(ctx, title, labels, a, b){

        var data = {
            labels: labels,
            datasets:[
                {
                    label: "Internal",
                    backgroundColor: rootObj.backgroundColors[0],
                    data: a
                },
                {
                    label: "External",
                    backgroundColor: rootObj.backgroundColors[1],
                    data: b
                },
            ]
        };

        var options = {
            legend: {
                display: true,
                position: "right"
            },
            title: {
                display: true,
                fontSize: 18,
                text: title
            },
            responsive: true,
            scales: {
                xAxes: [{
                    stacked: true,
                    scaleLabel: {
                        display: true,
                        labelString: "Builds",
                        fontSize: 15,
                        fontStyle: "italic"
                    },
                    barThickness: 15
                }],
                yAxes: [{
                    stacked: true,
                    scaleLabel: {
                        display: true,
                        labelString: "Machines",
                        fontSize: 15,
                        fontStyle: "italic"
                    }
                }]
            }
        };

        rootObj.newChart(ctx, "bar", data, options);
    }

    rootObj.renderMachinesPerBuild = renderChart;

});
