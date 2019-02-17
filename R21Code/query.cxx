#include <AsgTools/MessageCheck.h>
#include <analysis/query.h>
#include <xAODEventInfo/EventInfo.h>
#include <xAODJet/JetContainer.h>

#include <TTree.h>

query :: query (const std::string& name,
                                  ISvcLocator *pSvcLocator)
    : EL::AnaAlgorithm (name, pSvcLocator)
{
  // Here you put any code for the base initialization of variables,
  // e.g. initialize all pointers to 0.  This is also where you
  // declare all properties for your algorithm.  Note that things like
  // resetting statistics variables or booking histograms should
  // rather go into the initialize() function.
}

StatusCode query :: initialize ()
{
  // Here you do everything that needs to be done at the very
  // beginning on each worker node, e.g. create histograms and output
  // trees.  This method gets called before any input files are
  // connected.

  // Book a TTree
  // ANA_CHECK (book (TTree ("analysis", "My analysis ntuple")));
  // auto mytree = tree ("analysis");
  // mytree->Branch("JetPt", &_jetPt);
  {% for l in book_code %}
  {{l}}
  {% endfor %}

  return StatusCode::SUCCESS;
}

StatusCode query :: execute ()
{
  // Here you do everything that needs to be done on every single
  // events, e.g. read input variables, apply cuts, and fill
  // histograms and trees.  This is where most of your actual analysis
  // code will go.

  // retrieve the eventInfo object from the event store
  const xAOD::EventInfo *eventInfo = nullptr;
  ANA_CHECK (evtStore()->retrieve (eventInfo, "EventInfo"));
  ANA_MSG_INFO ("in execute, runNumber = " << eventInfo->runNumber() << ", eventNumber = " << eventInfo->eventNumber());

  // Loop over the jets, and print out some nice info.
  // const xAOD::JetContainer* jets = 0;
  // ANA_CHECK (evtStore()->retrieve( jets, "AntiKt4EMTopoJets")); // Make 'AnalysisJets_NOSYS' if systematics & calibration are being run
  //ANA_MSG_INFO ("execute(): number of jets = " << jets->size());

  // for (auto jet : *jets) {
  //     _jetPt = jet->pt();
  //     //ANA_MSG_INFO ("execute(): jet pt = " << (jet->pt() * 0.001) << " GeV"); // just to print out something
  //     tree("analysis")->Fill();
  // }

  {% for l in query_code %}
  {{l}}
  {% endfor %}

  return StatusCode::SUCCESS;
}



StatusCode query :: finalize ()
{
  // This method is the mirror image of initialize(), meaning it gets
  // called after the last event has been processed on the worker node
  // and allows you to finish up any objects you created in
  // initialize() before they are written to disk.  This is actually
  // fairly rare, since this happens separately for each worker node.
  // Most of the time you want to do your post-processing on the
  // submission node after all your histogram outputs have been
  // merged.
  return StatusCode::SUCCESS;
}