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


    function renderStats(ctx, labels, values){

        var data = {
            labels: labels,
            datasets: [{
                label: "Crash reports by classification",
                backgroundColor: rootObj.backgroundColors,
                data: values
            }]
        };

        var options = {
            title: {
                display: true,
                text: "Crash reports by classification",
                fontSize: 18,
            },
            legend: {
                position: 'right'
            }
        };

        rootObj.newChart(ctx, "pie", data, options);
    }


    function renderReports(ctx, labels, values){

        var data = {
            labels: labels,
            datasets:[
                {
                    label: "Crash reports by build",
                    backgroundColor: rootObj.backgroundColors[0],
                    data: values
                }
            ]
        };

        var options = {
            legend: { display: false },
            title: {
                display: true,
                text: "Crash reports by build",
                fontSize: 15
            },
            scales: {
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: "Crash count",
                        fontSize: 15,
                        fontStyle: "italic"
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

    rootObj.renderCrashStats = renderStats;
    rootObj.renderCrashReports = renderReports;
});
