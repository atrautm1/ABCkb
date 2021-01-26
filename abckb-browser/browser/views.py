from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponse
import random
import csv
import datetime
from . import QueryRunner, QueryBuilder

empty_query = [
    "You forgot to type something, silly goose",
    "You're killing me smalls",
    "Type your query here ... in this box ... up here",
    "Alright alright alright, we got a live one!"
]

runner = QueryRunner.QueryRunner()

def home(request):
    return render(request, "browser/index.html")

def about(request):
    return render(request, "browser/about.html")

def search(request):
    context = {}
    query = """CALL db.index.fulltext.queryNodes("NODE_NAMES_LWRCSE", "{}") YIELD node, score return node.name, node.synonyms, labels(node), score, node.source_id limit 10"""
    if request.method == "GET":
        term = request.GET.get("search-term")
        if not term:
            context["Q"] = random.choice(empty_query)
            return render(request, "browser/search.html", context)
        # runner = QueryRunner.QueryRunner()
        results = runner.run_query(query.format(term))
        rows = []
        for n,v in results.items():
            labels = [i for i in v["labels(node)"] if list(i)[0].isupper()]
            rows.append([v["node.source_id"],
                         v["node.name"],
                         " | ".join(v["node.synonyms"]),
                         " | ".join(labels)])
        context["Q"] = term
        context["header"] = ["ID", "Name","Synonyms","Node Labels"]
        context["rows"] = rows
    request.session["rows"] = rows
    request.session["Q"] = term
    return render(request, "browser/search.html", context)

def build(request):
    context = {}
    context["snows"] = []
    primary_node_labels = [label for label in runner.labels if list(label)[0].isupper()]
    if request.method == "POST":
        checkboxes = request.POST.getlist("checkboxes")
        if checkboxes:
            for i in checkboxes:
                row = request.session["rows"][int(i)-1]
                new_row = row[:2] + row[-1:]
                context["snows"].append(new_row)
    request.session["snows"] = context["snows"]
    context["header"] = ["ID", "Name", "Labels"]
    context["Q"] = request.session["Q"]
    context["open_header"] = ["Select", "Endpoint"]
    context["open_rows"] = primary_node_labels
    request.session["open_rows"] = primary_node_labels
    return render(request, "browser/builder.html", context)

def runquery(request):
    context = {}
    # Table header: Output node, Path, Source (Text-mined, hybrid, ) 
    # Buttons: View Cypher Query, Download CSV
    if request.method == "GET":
        discovery = "on" #request.GET["open_discovery"]
        if discovery == "on":
            label = request.GET["toLabel"]
            start_nodes = []
            for i in request.session["snows"]:
                start_nodes.append({"id":i[0],"label":i[2]})
        # Build the query
        builder = QueryBuilder.QueryBuilder()
        query = builder.build_query(start_nodes,label)
        results = runner.run_query(query[0]+" SKIP 0 LIMIT 10")
        rows = []
        # Iterate through results
        for n,v in results.items():
            # I <3 List Expressions
            # Grab only the (Primary) labels that start with an uppercase letter
            labels = [j for i in v["nods"] for j in i if list(j)[0].isupper()]
            rels = set(v["rels"])
            if len(rels) > 1:
                rel = "Hybrid"
            elif len(rels) == 1 and 'text_mined' in rels:
                rel = "Text Mined"
            else:
                rel = v["rels"][0]
            rows.append([n,
                         " -> ".join(v["nodNames"]),
                         rel,
                         " | ".join(labels)])
        context["header"] = ["ID", "Path","Source","Labels"]
        context["rows"] = rows
    request.session["rows"] = rows
    request.session["cypher-query"] = query[0]
    return render(request, "browser/query.html", context)

def viewcypher(request):
    context = {}
    context["cq"] = request.session["cypher-query"]
    return render(request, "browser/cypher.html", context)

def download(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="abckb_query_results.csv"'
    
    writer = csv.writer(response)
    today = datetime.date.today()
    writer.writerow([f"### Generated on: {today.ctime()}"])
    writer.writerow([f"### Generated with query: {request.session['cypher-query']}"])
    writer.writerow(["ID","Path","Relationship Source","Labels"])
    query = request.session["cypher-query"]
    results = runner.run_query(query)
    for n,v in results.items():
        # I <3 List Expressions
        # Grab only the (Primary) labels that start with an uppercase letter
        labels = [j for i in v["nods"] for j in i if list(j)[0].isupper()]
        rels = set(v["rels"])
        if len(rels) > 1:
            rel = "Hybrid"
        elif len(rels) == 1 and 'text_mined' in rels:
            rel = "Text Mined"
        else:
            rel = v["rels"][0]
        writer.writerow([str(n),
                    " -> ".join(v["nodNames"]),
                    rel,
                    " | ".join(labels)])
    return response