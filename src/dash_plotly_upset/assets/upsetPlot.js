(function () {
    "use strict";

    function boolValue(value) {
        return value === true || value === "true" || value === 1 || value === "1";
    }

    function computeExclusiveIntersections(items, setCols, minSize, topN) {
        const nSets = setCols.length;
        const rows = [];

        for (let number = 1; number < Math.pow(2, nSets); number++) {
            const bits = number.toString(2).padStart(nSets, "0");

            let size = 0;

            for (const item of items) {
                let match = true;

                for (let i = 0; i < nSets; i++) {
                    const col = setCols[i];
                    const expected = bits[i] === "1";
                    const observed = boolValue(item[col]);

                    if (observed !== expected) {
                        match = false;
                        break;
                    }
                }

                if (match) {
                    size += 1;
                }
            }

            if (size >= minSize) {
                const activeSets = [];
                const pattern = {};

                for (let i = 0; i < nSets; i++) {
                    const col = setCols[i];
                    const isActive = bits[i] === "1";
                    pattern[col] = isActive;

                    if (isActive) {
                        activeSets.push(col);
                    }
                }

                rows.push({
                    intersection_id: bits,
                    label: activeSets.join(" & "),
                    active_sets: activeSets,
                    degree: activeSets.length,
                    size: size,
                    pattern: pattern
                });
            }
        }

        rows.sort(function (a, b) {
            if (b.size !== a.size) {
                return b.size - a.size;
            }

            return b.degree - a.degree;
        });

        const limited = topN ? rows.slice(0, topN) : rows;

        for (let i = 0; i < limited.length; i++) {
            limited[i].x = i;
        }

        return limited;
    }

    function computeSetSizes(items, setCols) {
        const rows = [];

        for (const col of setCols) {
            let size = 0;

            for (const item of items) {
                if (boolValue(item[col])) {
                    size += 1;
                }
            }

            rows.push({
                set: col,
                size: size
            });
        }

        rows.sort(function (a, b) {
            return a.size - b.size;
        });

        return rows;
    }

    let computedCache = null;

    function computedKey(setCols, minSize, topN) {
        return setCols.join("\u001f") + "\u001e" + String(minSize) + "\u001e" + String(topN || "");
    }

    function computeUpSetData(items, setCols, minSize, topN) {
        const key = computedKey(setCols, minSize, topN);
        if (computedCache && computedCache.items === items && computedCache.key === key) {
            return computedCache.value;
        }
        const value = {
            intersections: computeExclusiveIntersections(items, setCols, minSize, topN),
            setSizes: computeSetSizes(items, setCols)
        };
        computedCache = {
            items: items,
            key: key,
            value: value
        };
        return value;
    }

    function intersectionXAxisRange(nIntersections) {
        if (nIntersections <= 3) {
            return [-0.75, Math.max(nIntersections - 0.25, 0.75)];
        }
        return [-0.75, nIntersections - 0.5];
    }

    function displaySetName(setName, nSets, labelMap) {
        const mapped = labelMap && labelMap[setName] ? labelMap[setName] : setName;
        const clean = String(mapped).replace(/^tuned\//, "");
        const qSweep = clean.match(/^q_(\d+(?:_\d+)?)__outlibq_(\d+(?:_\d+)?)$/);
        if (qSweep) {
            return "q " + compactDecimalToken(qSweep[1]) + " / lib " + compactDecimalToken(qSweep[2]);
        }
        if (nSets > 10) {
            return ellipsizeLabel(clean, 24);
        }
        return wrapSetLabel(clean, 18, 2);
    }

    function compactDecimalToken(token) {
        const normalized = String(token).replace(/_/g, ".");
        if (normalized.startsWith("0.")) {
            return normalized.slice(1);
        }
        return normalized;
    }

    function ellipsizeLabel(label, maxLength) {
        const text = String(label);
        if (text.length <= maxLength) {
            return text;
        }
        return text.slice(0, Math.max(maxLength - 3, 1)) + "...";
    }

    function wrapSetLabel(label, maxLineLength, maxLines) {
        const text = String(label);
        if (text.length <= maxLineLength) {
            return text;
        }

        const tokens = text
            .split(/[_/]+/)
            .filter(function (token) {
                return token.length > 0;
            });
        const lines = [];
        let current = "";

        for (const token of tokens) {
            const candidate = current ? current + "_" + token : token;
            if (candidate.length <= maxLineLength || current.length === 0) {
                current = candidate;
            } else {
                lines.push(current);
                current = token;
            }
        }
        if (current) {
            lines.push(current);
        }

        if (lines.length <= maxLines) {
            return lines.join("<br>");
        }

        const kept = lines.slice(0, maxLines);
        kept[maxLines - 1] = kept[maxLines - 1] + "...";
        return kept.join("<br>");
    }

    function focusIntersection(row, selected) {
        if (!selected) {
            return true;
        }

        if (selected.kind === "intersection") {
            return row.intersection_id === selected.id;
        }

        if (selected.kind === "set") {
            return row.pattern[selected.id] === true;
        }

        return true;
    }

    function focusSet(setName, selected, intersections) {
        if (!selected) {
            return true;
        }

        if (selected.kind === "set") {
            return setName === selected.id;
        }

        if (selected.kind === "intersection") {
            const row = intersections.find(function (r) {
                return r.intersection_id === selected.id;
            });

            if (!row) {
                return false;
            }

            return row.pattern[setName] === true;
        }

        return true;
    }

    function normalizeMultiSelections(value) {
        if (!Array.isArray(value)) {
            return [];
        }
        return value.filter(function (entry) {
            return entry && (entry.kind === "intersection" || entry.kind === "set") && entry.id !== undefined;
        }).slice(0, 5);
    }

    function multiSelectionFor(row, multiSelections) {
        return multiSelections.find(function (entry) {
            return entry.kind === "intersection" && String(entry.id) === String(row.intersection_id);
        }) || null;
    }

    function directMultiSelection(kind, id, multiSelections) {
        return multiSelections.find(function (entry) {
            return entry.kind === kind && String(entry.id) === String(id);
        }) || null;
    }

    function makeFigure(options) {
        const items = options.items || [];
        const setCols = options.setCols || [];
        const selected = options.selected || null;
        const multiSelections = normalizeMultiSelections(options.multiSelected || []);
        const minSize = options.minSize || 1;
        const topN = options.topN || null;
        const labelMap = options.labelMap || {};
        const plotStyle = options.plotStyle || "default";
        const labelScale = Math.min(Math.max(Number(options.labelScale || 1), 0.8), 1.8);
        const publicationMode = plotStyle === "publication";

        const computed = computeUpSetData(items, setCols, minSize, topN);
        const intersections = computed.intersections;
        const setSizes = computed.setSizes;

        const matrixSetOrder = setSizes.map(function (d) {
            return d.set;
        });
        const nSets = Math.max(matrixSetOrder.length, 1);
        const displayNameBySet = {};

        for (const setName of matrixSetOrder) {
            displayNameBySet[setName] = displaySetName(setName, nSets, labelMap);
        }

        function displayIntersectionLabel(row) {
            return row.active_sets.map(function (setName) {
                return String(displayNameBySet[setName] || setName).replace(/<br>/g, " ");
            }).join(" & ");
        }

        const data = [];

        if (intersections.length === 0) {
            return {
                data: [],
                layout: {
                    template: "plotly_white",
                    height: 570,
                    margin: {
                        l: 30,
                        r: 24,
                        t: 78,
                        b: 24
                    },
                    annotations: [
                        {
                            text: "No intersections found with the current filters.",
                            x: 0.5,
                            y: 0.5,
                            xref: "paper",
                            yref: "paper",
                            showarrow: false,
                            font: {
                                size: 15,
                                color: "#333333"
                            }
                        }
                    ]
                }
            };
        }

        const nIntersections = intersections.length;
        const xRange = intersectionXAxisRange(nIntersections);
        const hasSelection = selected !== null && selected !== undefined;
        const hasMultiSelection = multiSelections.length > 0;

        // ----------------------------------------------------
        // Top intersection bars
        // ----------------------------------------------------

        const barX = intersections.map(function (d) {
            return d.x;
        });

        const barY = intersections.map(function (d) {
            return d.size;
        });

        const barColors = intersections.map(function (d) {
            const multi = multiSelectionFor(d, multiSelections);
            if (multi) {
                return multi.color || "#2563eb";
            }
            if (hasMultiSelection) {
                return "#D6D9DE";
            }
            return focusIntersection(d, selected) ? "#111827" : (publicationMode ? "#D1D5DB" : "#CFCFCF");
        });

        const barLineWidths = intersections.map(function (d) {
            if (multiSelectionFor(d, multiSelections)) {
                return 2.5;
            }
            if (!hasSelection) {
                return 0;
            }

            if (selected.kind === "intersection" && d.intersection_id === selected.id) {
                return 2.5;
            }

            return 0;
        });

        const intersectionCustomData = intersections.map(function (d) {
            return ["intersection", d.intersection_id, displayIntersectionLabel(d)];
        });

        data.push({
            type: "bar",
            x: barX,
            y: barY,
            width: 0.65,
            xaxis: "x2",
            yaxis: "y2",
            marker: {
                color: barColors,
                line: {
                    color: "#111111",
                    width: barLineWidths
                }
            },
            text: barY.map(String),
            textposition: "outside",
            textfont: {
                size: Math.round(11 * labelScale),
                color: "#111827"
            },
            cliponaxis: false,
            customdata: intersectionCustomData,
            hovertemplate:
                "<b>Click to select intersection</b><br>" +
                "Intersection: %{customdata[2]}<br>" +
                "ID: %{customdata[1]}<br>" +
                "Items: %{y}<extra></extra>",
            name: "Intersection size"
        });

        // ----------------------------------------------------
        // Left set-size bars
        // ----------------------------------------------------

        const setNames = setSizes.map(function (d) {
            return d.set;
        });

        const setValues = setSizes.map(function (d) {
            return d.size;
        });

        const setBarColors = setNames.map(function (setName) {
            const direct = directMultiSelection("set", setName, multiSelections);
            if (direct) {
                return direct.color || "#2563eb";
            }
            if (hasMultiSelection) {
                const covered = multiSelections.some(function (entry) {
                    if (entry.kind === "set") {
                        return String(entry.id) === String(setName);
                    }
                    const row = intersections.find(function (d) {
                        return String(d.intersection_id) === String(entry.id);
                    });
                    return row && row.pattern[setName] === true;
                });
                return covered ? "#6B7280" : "#D6D9DE";
            }
            return focusSet(setName, selected, intersections) ? "#111827" : (publicationMode ? "#D1D5DB" : "#CFCFCF");
        });

        const setBarLineWidths = setNames.map(function (setName) {
            if (directMultiSelection("set", setName, multiSelections)) {
                return 2.5;
            }
            if (!hasSelection) {
                return 0;
            }

            if (selected.kind === "set" && selected.id === setName) {
                return 2.5;
            }

            return 0;
        });

        const setCustomData = setNames.map(function (setName) {
            return ["set", setName, String(displayNameBySet[setName] || setName).replace(/<br>/g, " ")];
        });

        const plotHeight = Math.max(620, 500 + nSets * 32);
        const labelFontSize = Math.round((nSets > 14 ? 10 : 11) * labelScale);
        const tickFontSize = Math.round(11 * labelScale);
        const titleFontSize = Math.round(18 * labelScale);
        const subtitleFontSize = Math.round(12 * labelScale);
        const setSizeDomainEnd = 0.30;
        const matrixDomainStart = 0.38;
        const labelX = matrixDomainStart - 0.012;

        data.push({
            type: "bar",
            orientation: "h",
            x: setValues,
            y: setNames,
            xaxis: "x3",
            yaxis: "y3",
            marker: {
                color: setBarColors,
                line: {
                    color: "#111827",
                    width: setBarLineWidths
                }
            },
            text: setValues.map(String),
            textposition: "outside",
            insidetextanchor: "end",
            textfont: {
                size: Math.round(11 * labelScale),
                color: "#111827"
            },
            cliponaxis: false,
            customdata: setCustomData,
            hovertemplate:
                "<b>Click to select set</b><br>" +
                "Set: %{customdata[2]}<br>" +
                "Items: %{x}<extra></extra>",
            name: "Set size"
        });

        // ----------------------------------------------------
        // Dot matrix
        // ----------------------------------------------------

        for (const row of intersections) {
            const x = row.x;
            const iid = row.intersection_id;
            const label = displayIntersectionLabel(row);

            const isFocusCol = focusIntersection(row, selected);
            const isSelectedCol =
                hasSelection &&
                selected.kind === "intersection" &&
                selected.id === iid;
            const multiSelection = multiSelectionFor(row, multiSelections);
            const isMultiSelectedCol = multiSelection !== null;
            const multiColor = isMultiSelectedCol ? (multiSelection.color || "#2563eb") : null;
            const multiDim = hasMultiSelection && !isMultiSelectedCol;

            const activeColor = isMultiSelectedCol ? multiColor : (isFocusCol ? "#111827" : "#BDBDBD");
            const inactiveColor = isMultiSelectedCol ? "#F0F3F7" : (isFocusCol ? "#D0D0D0" : "#EEEEEE");
            const lineColor = isMultiSelectedCol ? multiColor : (isFocusCol ? "#111827" : "#BDBDBD");
            const opacity = multiDim ? 0.24 : (isFocusCol ? 1.0 : 0.28);

            const activeSets = matrixSetOrder.filter(function (setName) {
                return row.pattern[setName] === true;
            });

            const inactiveSets = matrixSetOrder.filter(function (setName) {
                return row.pattern[setName] !== true;
            });

            if (activeSets.length >= 2) {
                data.push({
                    type: "scatter",
                    mode: "lines",
                    x: [x, x],
                    y: [activeSets[0], activeSets[activeSets.length - 1]],
                    xaxis: "x4",
                    yaxis: "y4",
                    line: {
                        color: lineColor,
                        width: isSelectedCol ? 2.8 : 1.9
                    },
                    opacity: opacity,
                    hoverinfo: "skip",
                    showlegend: false
                });
            }

            if (inactiveSets.length > 0) {
                data.push({
                    type: "scatter",
                    mode: "markers",
                    x: inactiveSets.map(function () {
                        return x;
                    }),
                    y: inactiveSets,
                    xaxis: "x4",
                    yaxis: "y4",
                    marker: {
                        size: 7,
                        color: inactiveColor,
                        line: {
                            color: inactiveColor,
                            width: 0
                        }
                    },
                    opacity: opacity,
                    customdata: inactiveSets.map(function (setName) {
                        return ["intersection", iid, label, String(displayNameBySet[setName] || setName).replace(/<br>/g, " ")];
                    }),
                    hovertemplate:
                        "<b>Click to select intersection</b><br>" +
                        "Intersection: %{customdata[2]}<br>" +
                        "ID: %{customdata[1]}<br>" +
                        "Set: %{customdata[3]}<br>" +
                        "Included: no<extra></extra>",
                    showlegend: false
                });
            }

            if (activeSets.length > 0) {
                data.push({
                    type: "scatter",
                    mode: "markers",
                    x: activeSets.map(function () {
                        return x;
                    }),
                    y: activeSets,
                    xaxis: "x4",
                    yaxis: "y4",
                    marker: {
                        size: isSelectedCol ? 13 : 11,
                        color: activeColor,
                        line: {
                            color: isMultiSelectedCol ? multiColor : "#111827",
                            width: isSelectedCol || isMultiSelectedCol ? 2.5 : 0
                        }
                    },
                    opacity: opacity,
                    customdata: activeSets.map(function (setName) {
                        return ["intersection", iid, label, String(displayNameBySet[setName] || setName).replace(/<br>/g, " ")];
                    }),
                    hovertemplate:
                        "<b>Click to select intersection</b><br>" +
                        "Intersection: %{customdata[2]}<br>" +
                        "ID: %{customdata[1]}<br>" +
                        "Set: %{customdata[3]}<br>" +
                        "Included: yes<extra></extra>",
                    showlegend: false
                });
            }
        }

        // ----------------------------------------------------
        // Subtitle
        // ----------------------------------------------------

        let subtitle = "Click an intersection bar, dot, or set-size bar to inspect its items.";

        if (hasMultiSelection) {
            subtitle = "Multi selections: " + multiSelections.length + "/5 selected. Click a selected intersection or set again to remove it.";
        }

        if (selected && !hasMultiSelection) {
            if (selected.kind === "intersection") {
                const row = intersections.find(function (d) {
                    return d.intersection_id === selected.id;
                });

                if (row) {
                    subtitle = "Selected intersection: " + row.label + " — " + row.size + " items";
                } else {
                    subtitle = "Selected intersection is not visible with the current filters.";
                }
            }

            if (selected.kind === "set") {
                const setSize = setSizes.find(function (d) {
                    return d.set === selected.id;
                });

                if (setSize) {
                    subtitle = "Selected set: " + displaySetName(selected.id, nSets, labelMap) + " — " + setSize.size + " items";
                }
            }
        }

        // ----------------------------------------------------
        // Layout
        // ----------------------------------------------------

        const layout = {
            template: "plotly_white",
            font: {
                family: publicationMode ? "Arial, Helvetica, sans-serif" : undefined,
                size: tickFontSize,
                color: "#111827"
            },
            title: {
                text: "Interactive UpSet plot",
                x: 0.02,
                xanchor: "left",
                font: {
                    size: titleFontSize,
                    color: "#111827"
                }
            },
            height: plotHeight,
            margin: {
                l: 30,
                r: 30,
                t: 78,
                b: 34
            },
            showlegend: false,
            bargap: 0.28,
            plot_bgcolor: "white",
            paper_bgcolor: "white",
            hoverlabel: {
                bgcolor: "white",
                font_size: Math.round(12 * labelScale),
                font_color: "#111827",
                bordercolor: "#BBBBBB"
            },
            clickmode: "event+select",
            dragmode: false,
            annotations: [
                {
                    text: subtitle,
                    x: 0.02,
                    y: 1.06,
                    xref: "paper",
                    yref: "paper",
                    showarrow: false,
                    align: "left",
                    font: {
                        size: subtitleFontSize,
                        color: publicationMode ? "#374151" : "#444444"
                    }
                },
                {
                    text: "Search",
                    x: labelX,
                    y: 0.375,
                    xref: "paper",
                    yref: "paper",
                    xanchor: "right",
                    yanchor: "bottom",
                    showarrow: false,
                    align: "right",
                    font: {
                        size: labelFontSize,
                        color: publicationMode ? "#374151" : "#555555"
                    }
                }
            ].concat(matrixSetOrder.map(function (setName) {
                return {
                    text: displayNameBySet[setName],
                    x: labelX,
                    y: setName,
                    xref: "paper",
                    yref: "y4",
                    xanchor: "right",
                    yanchor: "middle",
                    showarrow: false,
                    align: "right",
                    font: {
                        size: labelFontSize,
                        color: "#111827"
                    },
                    hovertext: setName,
                    hoverlabel: {
                        bgcolor: "white"
                    }
                };
            })),

            // x2/y2 = top-right intersection bars
            xaxis2: {
                anchor: "y2",
                domain: [matrixDomainStart, 1.0],
                range: xRange,
                fixedrange: true,
                showticklabels: false,
                showgrid: false,
                zeroline: false,
                showline: false
            },
            yaxis2: {
                anchor: "x2",
                domain: [0.42, 1.0],
                title: {
                    text: "Intersection size",
                    font: {
                        size: Math.round(12 * labelScale)
                    }
                },
                showgrid: true,
                gridcolor: publicationMode ? "#E5E7EB" : "#E8E8E8",
                zeroline: false,
                showline: true,
                linecolor: "#111827",
                ticks: "outside",
                tickfont: {
                    size: tickFontSize
                }
            },

            // x3/y3 = bottom-left set-size bars
            xaxis3: {
                anchor: "y3",
                domain: [0.0, setSizeDomainEnd],
                title: {
                    text: "Set size",
                    font: {
                        size: Math.round(12 * labelScale)
                    }
                },
                showgrid: true,
                gridcolor: publicationMode ? "#E5E7EB" : "#E8E8E8",
                zeroline: false,
                showline: true,
                linecolor: "#111827",
                ticks: "outside",
                tickfont: {
                    size: tickFontSize
                },
                automargin: false,
                autorange: "reversed"
            },
            yaxis3: {
                anchor: "x3",
                domain: [0.0, 0.34],
                showticklabels: false,
                showgrid: false,
                zeroline: false,
                showline: false,
                tickfont: {
                    size: tickFontSize,
                    color: "#111827"
                },
                categoryorder: "array",
                categoryarray: matrixSetOrder
            },

            // x4/y4 = bottom-right dot matrix
            xaxis4: {
                anchor: "y4",
                domain: [matrixDomainStart, 1.0],
                range: xRange,
                fixedrange: true,
                showticklabels: false,
                showgrid: false,
                zeroline: false,
                showline: false
            },
            yaxis4: {
                anchor: "x4",
                domain: [0.0, 0.34],
                showticklabels: false,
                showgrid: false,
                zeroline: false,
                showline: false,
                ticks: "",
                tickfont: {
                    size: labelFontSize,
                    color: "#111827"
                },
                automargin: false,
                categoryorder: "array",
                categoryarray: matrixSetOrder
            }
        };

        return {
            data: data,
            layout: layout
        };
    }

    window.upsetPlot = {
        makeFigure: makeFigure,
        computeExclusiveIntersections: computeExclusiveIntersections,
        computeSetSizes: computeSetSizes
    };
})();
