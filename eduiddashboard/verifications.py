from eduiddashboard.utils import get_unique_hash


def get_verification_code(db, model_name, obj_id):
    results = db.verifications.find({'obj_id': obj_id, 'model_name': model_name})
    return results[0]


def new_verification_code(db, model_name, obj_id, user, hasher=None):
    if hasher is None:
        hasher = get_unique_hash
    code = hasher()
    obj = {
        "model_name": model_name,
        "obj_id": obj_id,
        "verified": False,
        "user_oid": user['_id'],
    }
    db.verifications.find_and_modify(
        obj,
        {"$set": {"code": code}},
        upsert=True,
        safe=True,
    )
    return code


def verificate_code(request, model_name, code):
    from eduiddashboard.views.emails import mark_as_verified_email
    from eduiddashboard.views.mobiles import mark_as_verified_mobile

    verifiers = {
        'email': mark_as_verified_email,
        'mobile': mark_as_verified_mobile,
    }

    result = request.db.verifications.find_and_modify(
        {
            "model_name": model_name,
            "code": code,
            "verified": False
        }, {
            "$set": {
                "verified": True
            }
        },
        new=True,
        safe=True
    )
    if not result:
        return None
    obj_id = result['obj_id']
    if obj_id:
        user = request.userdb.get_user_by_oid(result['user_oid'])
        # Callback to a function which marks as verificated the proper user attribute
        verifiers[model_name](request, user, obj_id)
        # Do the save staff
        request.db.profiles.save(user, safe=True)
        request.context.propagate_user_changes(user)
    return obj_id


def generate_verification_link(request, db, model, obj_id):
    code = new_verification_code(db, model, obj_id, request.context.user)
    link = request.route_url("verifications", model=model, code=code)
    return link
