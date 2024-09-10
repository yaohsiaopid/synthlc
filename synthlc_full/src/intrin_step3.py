import os
from gconsts import *
from util import *
from IFT_template import *
from csv_util import *
# just entire group first
def intrin_step3_proc(
    i_p_instns,
    field_i_p,
    BATCH_INSTNDIR,
    i_p_id,
    i0_constraint,
    decision_src, 
    div_node_all_uniq_pl_iso, 
    cnt_follower_sets,
    group_items_transmitter
    ):
    uniq_pl_in_all_pl_set = sorted(div_node_all_uniq_pl_iso[decision_src])
    # iter over each decision for thie decision_src
    for pairafset in cnt_follower_sets:
        cnt, afset = pairafset
        afset = sorted(afset)
        followerset = "("
        if not decision_src in afset:
            followerset += "!{node} && ".format(node=transform_disjunc(decision_src))
        for eachN in uniq_pl_in_all_pl_set:
            if eachN == "":
                continue
            followerset += "{ina}{node} && ".format(
                    node = transform_disjunc(eachN),
                    ina = ("" if (eachN in afset) else "!")
            )
     
        followerset += " 1'b1)"
        if len(afset) == 0:
            t0 = "|{"
            for eachN in uniq_pl_in_all_pl_set:
                if eachN == "":
                    continue
                t0 += (transform_iso_t0_neg(eachN, decision_src) + " ,")
            t0 += "1'b0}"

        else:
            t0 = "|{"
            for eachN in afset:
                t0 += (transform_iso_t0(eachN) + " ,") # + "_t0 ,")
            t0 += "1'b0}"

        # for this given decision_src, afset

        org_dir = "group_{I}_IFT/itself".format(I=i_p_id)
        tar_dir = "group_{I}_IFT/itself_per".format(I=i_p_id)
        prep_dir(tar_dir + "/out")
        TFIELD="bothrs_"
        DEFINEOPTAINT="`define BORTHRS"
        if field_i_p == "rs1":
            TFIELD="rs1_"
            DEFINEOPTAINT="`define RS1"

        # decision idx
        csvf ="{tdir}/{ID}_g.csv".format(tdir=org_dir, ID=cnt)

        if not os.path.exists(csvf):
            assert(0)
        df = pd.read_csv(csvf, dtype=mydtypes)

        res, bnd, time = df_query(df, "DEP_%s" % (TFIELD + str(cnt)))
        if res == "covered":
            if not TFIELD=="bothrs_": 
                continue
            for i_p in i_p_instns:
                i0_constraint = get_i_constraint_indep(i_p, "i0")
                csvf ="{tdir}/{ID}_{i_p}.csv".format(tdir=org_dir, ID=cnt, i_p=i_p)
                df = pd.read_csv(csvf, dtype=mydtypes)
                res, bnd, time = df_query(df, "DEP_%s" % (TFIELD + str(cnt)))
        
                # TODO skip
                skip = False
                if i_p in ["SW", "SB", "SD", "SH"]:
                    skip = True
                    if len(afset) == 0:
                        rs1, rs2 = skip_ufsm_based([i_p], uniq_pl_in_all_pl_set)
                    else:
                        rs1, rs2 = skip_ufsm_based([i_p], afset)
                    assert (rs1 == False and rs2 == True) 
                if res == "covered" and (not skip):
                    for tag, deft in zip(["rs1", "rs2"], ["`define RS1", "`define RS2"]):
                        outfilename="{tdir}/out/{ID}_{i_p}_{tag}.sv".format(tdir=tar_dir, ID=cnt, i_p=i_p, tag=tag)
                        outstring = itself_template_prop 
                        rep_pairs = [ 
                            ("OP_TAINT", deft), 
                            ("INSTN_CONSTRAINT", i0_constraint),
                            ("DECNODE", transform_disjunc(decision_src)),
                            ("FOLLOWERSET", followerset),
                            ("FIELD",  TFIELD + str(cnt)),
                            ("TT0", t0),
                            ]
                        for tt in rep_pairs:
                            outstring = outstring.replace(tt[0], tt[1])
                        with open(outfilename, "w") as f:
                            f.write(outstring)

    cmd = "python3 host_batch_run_template_v2.py group_{groupid}_IFT/itself_per group_{groupid}_IFT/itself_per/out".format(groupid=i_p_id)
    return cmd
