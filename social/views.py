from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from social.forms import *
from social.models import *
from datetime import datetime
from django.utils import simplejson
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.utils.http import urlunquote_plus

import json
import social.timeline as timeline

def main_page(request):
    return render_to_response('main_page.html',RequestContext(request))

#def user_page(request, username):
#    try:
#        user = User.objects.get(username=username)
#    except User.DoesNotExist:
#        raise Http404(u'Requested user not found.')
#
#    fullname = user.get_full_name()
#
#    variables = RequestContext(request, {
#            'username': username,
#            'fullname': fullname
#    })
#    return render_to_response('user_page.html', variables)

def logout_page(request):
    logout(request)
    if request.GET.has_key("next"):
        return HttpResponseRedirect(request.GET['next'])
    return HttpResponseRedirect(reverse('carnatic-overview'))

def register_page(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
            )
            
            user.save()
            
            return HttpResponseRedirect(reverse('social-auth-register-success'))
    else:
        form = RegistrationForm()
    variables = RequestContext(request, {
            'form': form
    })
    return render_to_response('registration/register.html',variables)

def user_profile(request):
    user_profile = request.user.get_profile()
    
    users_id = []
    users_id.append(request.user.id)
    
    timelines = timeline.timeline(users_id)
    
    variables = RequestContext(request, {
        'user_profile': user_profile,
        'timeline': timelines
    })
    return render_to_response('user-profile.html', variables)


def user_profile_save(request):
    user_profile = request.user.get_profile()
    if request.method == 'POST':
        form = UserProfileForm(request.POST)

    else:
        form = UserProfileForm()
    
    variables = RequestContext(request, {
        'user_profile': user_profile
    })
    return render_to_response('user-profile.html', variables)

def users_list(request):
    numusers = User.objects.count()
    users = User.objects.all()

    ret = {"numusers": numusers,
           "users": users,
           }
    return render(request, "users_list.html", ret)

def user_page(request, username):
    other_user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user_id=other_user.id)
    
    user = request.user
    if len(UserFollowsUser.objects.filter(user_follower_id=user, user_followed_id=other_user)) == 0:
        follow = False
    else:
        follow = True
    
    
    users_id = []
    users_id.append(other_user.id)
    
    timelines = timeline.timeline(users_id)
    
    
    ret = {"other_user": other_user,
           "profile": profile,
           "timeline": timelines,
           "follow": follow
    }

    return render(request, "user_page.html", ret)

@csrf_protect
def user_follow(request):
    to_follow = get_object_or_404(User, username=request.POST['username'])
    follower = request.user
    user_follows_user, _ = UserFollowsUser.objects.get_or_create(user_follower=follower, user_followed=to_follow, timestamp=datetime.now())
    ret = {"status": "OK"}
    return HttpResponse(json.dumps(ret), content_type="application/json")

@csrf_protect
def user_unfollow(request):
    to_unfollow = get_object_or_404(User, username=request.POST['username'])
    follower = request.user
    print follower, to_unfollow
    user_follows_user = UserFollowsUser.objects.filter(user_follower=follower, user_followed=to_unfollow)
    if len(user_follows_user) == 0:
        ret = {"status": "FAIL"}
    else:
        user_follows_user.delete()
        ret = {"status": "OK"}
    return HttpResponse(json.dumps(ret), content_type="application/json")

##### TAG ####

def tag_save_page(request):
    if request.method == 'POST':
        form = TagSaveForm(request.POST)
        if form.is_valid():
            # Create new tag list.
            objectid = int(form.cleaned_data['objectid'])
            objecttype = form.cleaned_data['objecttype']
            tag_names = form.cleaned_data['tags'].split(",")
            for tag_name in tag_names:
                if len(tag_name) > 0:
                    tag, _ = Tag.objects.get_or_create(name=tag_name.lower().strip()) # tag to lower case
                    
                    if objecttype == "artist":
                        artist = Artist.objects.get(pk=objectid)
                        if len(ArtistTag.objects.filter(tag=tag, user=request.user, artist=artist)) == 0:
                            object_tag, _ = ArtistTag.objects.get_or_create(tag=tag, user=request.user, artist=artist, timestamp=datetime.now())
                    elif objecttype == "concert":
                        concert = Concert.objects.get(pk=objectid)
                        if len(ConcertTag.objects.filter(tag=tag, user=request.user, concert=concert)) == 0:
                            object_tag, _ = ConcertTag.objects.get_or_create(tag=tag, user=request.user, concert=concert, timestamp=datetime.now())
                    elif objecttype == "recording":
                        recording = Recording.objects.get(pk=objectid)
                        if len(RecordingTag.objects.filter(tag=tag, user=request.user, recording=recording)) == 0:
                            object_tag, _ = RecordingTag.objects.get_or_create(tag=tag, user=request.user, recording=recording, timestamp=datetime.now())
                    elif objecttype == "work":
                        work = Work.objects.get(pk=objectid)
                        if len(WorkTag.objects.filter(tag=tag, user=request.user, work=work)) == 0:
                            object_tag, _ = WorkTag.objects.get_or_create(tag=tag, user=request.user, work=work, timestamp=datetime.now())
            
            return HttpResponseRedirect('/carnatic/%s/%s' % (objecttype, objectid))
    else:
        form = TagSaveForm()
    variables = RequestContext(request, {
        'form': form
    })
    return render_to_response('form-tag.html', variables)


def ajax_tag_autocomplete(request):
    q = request.GET['term']
    tags = Tag.objects.filter(name__istartswith=q)[:10]
    results = []
    for tag in tags:
        tag_dict = {'id':tag.id, 'label':tag.name, 'value':tag.name}
        results.append(tag_dict)
    return HttpResponse(simplejson.dumps(results),mimetype='application/json')


def tag_page(request, tagname, modeltype="concert"):
    tagname = urlunquote_plus(tagname)
    tag = get_object_or_404(Tag, name=tagname)
    
    if modeltype == "artist":
        lists = ArtistTag.objects.filter(tag__name=tagname).values('artist', 'tag').annotate(freq=Count('artist'))
        objects=[]
        for lista in lists:
            objects.append([Artist.objects.get(pk=lista['artist']), lista['freq']])
    elif modeltype == "concert":
        lists = ConcertTag.objects.filter(tag__name=tagname).values('concert', 'tag').annotate(freq=Count('concert'))
        objects=[]
        for lista in lists:
            objects.append([Concert.objects.get(pk=lista['concert']), lista['freq']])
    elif modeltype == "recording":
        lists = RecordingTag.objects.filter(tag__name=tagname).values('recording', 'tag').annotate(freq=Count('recording'))
        objects=[]
        for lista in lists:
            objects.append([Recording.objects.get(pk=lista['recording']), lista['freq']])
    elif modeltype == "work":
        lists = WorkTag.objects.filter(tag__name=tagname).values('work', 'tag').annotate(freq=Count('work'))
        objects=[]
        for lista in lists:
            objects.append([Work.objects.get(pk=lista['work']), lista['freq']])
      
    variables = RequestContext(request, {
        'objects': objects,
        'tag_name': tagname,
        'modeltype': modeltype,
    })
    return render_to_response('tag_page.html', variables)


