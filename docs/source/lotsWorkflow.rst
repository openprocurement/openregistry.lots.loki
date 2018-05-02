.. _lots_workflow:

Lots Workflow
==============

.. graphviz::

    digraph G {
            subgraph cluster_1 {
                    node [style=filled, fillcolor=seashell2];
                    edge[style=dashed,  arrowhead="vee"];
                    "draft" -> "composing" [color="0.6667 1.0000 0.5020"];
                    edge[style=dashed,  arrowhead="vee"];
                    "composing" -> "verification" [color="0.6667 1.0000 0.5020"];
                    edge[style=solid,  arrowhead="vee"];
                    "verification" -> "pending" [color="0.6667 1.0000 0.5020"];
                    edge[style=dashed,  arrowhead="vee"];
                    "pending" -> "active.salable" [color="0.6667 1.0000 0.5020"];
                    edge[style=solid,  dir="both"];
                    "active.salable" -> "active.auction" [color="0.6667 1.0000 0.5020"];
                    edge[dir="forward"];
                    "active.auction" -> "active.contracting" [color="0.6667 1.0000 0.5020"];
                    edge[dir="forward"];
                    "active.contracting" -> "pending.sold" [color="0.6667 1.0000 0.5020"];
                    edge[dir="forward"];
                    "pending.sold" -> "sold" [color="0.6667 1.0000 0.5020"];
                    color=white;
            } 

            edge[style=solid, arrowhead="vee"]
            "verification" -> "invalid" [color="0.0000 0.0000 0.3882"];
            edge[style=dashed, arrowhead="vee"]
            "pending" -> "deleted" [color="0.0000 0.0000 0.3882"];
            edge[style=solid];
            node [style=solid];
            edge[style=solid];
            "active.auction" -> "pending.dissolution" [color="0.0000 0.0000 0.3882"];
            edge[style=solid];
            "active.contracting" -> "pending.dissolution" [color="0.0000 0.0000 0.3882"];
            edge[style=solid];
            node [style=solid];
            "pending.dissolution" -> "dissolved" [color="0.0000 0.0000 0.3882"];
    }

Legend
--------

   * dashed line - user action
    
   * solid line - action is done automatically
