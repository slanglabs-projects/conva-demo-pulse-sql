from typing import Dict, Any
import plotly.graph_objects as go


def create_plot(data_dict: Dict[str, Any]) -> go.Figure:
    """
    Creates a Plotly figure based on input data dictionary.
    Uses pastel colors for better visibility on dark background.

    Args:
        data_dict: Dictionary with keys:
            - type: "line" or "bar"
            - xaxis_title: str
            - yaxis_title: str
            - legends: list[str]
            - series_data: dict

    Returns:
        go.Figure: Plotly figure object
    """
    fig = go.Figure()
    # Pastel colors that work well on dark background
    colors = [
        '#7CB9E8',  # Light blue
        '#FFB3BA',  # Pastel pink
        '#BAFCA2',  # Pastel green
        '#FFD7AA',  # Pastel orange
        '#E0BBE4',  # Pastel purple
        '#957DAD'  # Muted purple
    ]

    x_values = list(data_dict["series_data"].keys())

    def to_float(val):
        """Convert string or number to float."""
        return float(val) if val is not None else None

    if data_dict["type"] == "line":
        first_val = next(iter(data_dict["series_data"].values()))
        if isinstance(first_val, (int, float, str)):
            y_values = [to_float(v) for v in data_dict["series_data"].values()]
            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    name=data_dict["legends"][0],
                    mode='lines+markers',
                    line=dict(color=colors[0], width=3),
                    marker=dict(size=8)
                )
            )
        else:
            for idx, legend in enumerate(data_dict["legends"]):
                if isinstance(first_val, dict):
                    y_values = [to_float(data_dict["series_data"][x][legend]) for x in x_values]
                else:
                    y_values = [to_float(data_dict["series_data"][x][idx]) for x in x_values]

                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_values,
                        name=legend,
                        mode='lines+markers',
                        line=dict(color=colors[idx % len(colors)], width=3),
                        marker=dict(size=8),
                        yaxis="y2" if idx > 0 and len(data_dict["legends"]) > 1 else "y"
                    )
                )

            if len(data_dict["legends"]) > 1:
                fig.update_layout(
                    yaxis2=dict(
                        overlaying='y',
                        side='right',
                        showgrid=False,
                        showline=True,
                        color='white'
                    )
                )

    else:  # bar chart
        first_val = next(iter(data_dict["series_data"].values()))
        if isinstance(first_val, (int, float, str)):
            y_values = [to_float(v) for v in data_dict["series_data"].values()]
            fig.add_trace(
                go.Bar(
                    x=x_values,
                    y=y_values,
                    marker_color=colors[0]  # noqa
                )
            )
        else:
            # Get all available keys from the first data point
            available_keys = list(first_val.keys())

            for idx, legend in enumerate(data_dict["legends"]):
                if isinstance(first_val, dict):
                    # Use positional mapping instead of exact key matching
                    key = available_keys[idx]
                    y_values = [to_float(data_dict["series_data"][x][key]) for x in x_values]
                else:
                    y_values = [to_float(data_dict["series_data"][x][idx]) for x in x_values]

                fig.add_trace(
                    go.Bar(
                        name=legend,
                        x=x_values,
                        y=y_values,
                        marker_color=colors[idx % len(colors)]  # noqa
                    )
                )
            fig.update_layout(barmode='group')

    fig.update_layout(
        title=f"{data_dict['xaxis_title']} vs {data_dict['yaxis_title']}",
        xaxis_title=data_dict["xaxis_title"],
        yaxis_title=data_dict["yaxis_title"],
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white'),
        showlegend=True,
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showline=True,
            color='white',
            tickmode='array',
            ticktext=x_values,
            tickvals=x_values,
            type='category'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showline=True,
            color='white'
        )
    )

    return fig